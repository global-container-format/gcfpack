"""GCF file packaging."""

from functools import reduce
from typing import Iterable, Tuple, Union, cast

from gcf import ContainerFlags, Header, ResourceType, SupercompressionScheme, Format
from gcf import blob as gcfblob
from gcf import compression
from gcf import texture as gcftex

from .meta import BlobResource as RawBlobResource
from .meta import GcfFlagValue as RawContainerFlags
from .meta import TextureMipLevel as RawTextureMipLevel
from .meta import TextureResource as RawTextureResource
from .meta import Metadata as RawGcfDescription
from .meta import Resource as RawResource
from .meta import SuperCompressionScheme as RawSupercompressionScheme


def deserialize_container_flags(raw: Iterable[RawContainerFlags]) -> ContainerFlags:
    """Deserialize a sequence of container flags."""

    result: ContainerFlags = ContainerFlags(0)

    for flag in raw:
        if flag == "unpadded":
            result |= ContainerFlags.UNPADDED
        else:
            raise ValueError("Invalid container flag.", flag)

    return result


def deserialize_supercompression_scheme(raw: RawSupercompressionScheme) -> SupercompressionScheme:
    """Deserialize a supercompression scheme value."""

    if raw == "none":
        return SupercompressionScheme.NO_COMPRESSION

    if raw == "deflate":
        return SupercompressionScheme.DEFLATE

    if raw == "test":
        return SupercompressionScheme.TEST

    if raw == "zlib":
        return SupercompressionScheme.ZLIB

    raise ValueError("Invalid supercompression scheme", raw)


def get_resource_type(res: RawResource) -> ResourceType:
    """Get the resource type from a raw resource."""

    res_type = res["type"]

    if res_type == "blob":
        return ResourceType.BLOB

    if res_type == "texture":
        return ResourceType.TEXTURE

    raise ValueError("Invalid resource type.", res_type)


def create_header(desc: RawGcfDescription) -> Header:
    """Create a GCF header from its raw description."""

    raw_header = desc["header"]
    gcf_version = raw_header["version"]
    flags = deserialize_container_flags(desc["header"].get("flags", []))

    return Header(len(desc["resources"]), flags, gcf_version)


def deserialize_format(raw_format: Union[str, int]) -> int:
    """Deserialize a raw format representation into a numeric format value."""

    if isinstance(raw_format, str):
        return Format[raw_format].value

    return raw_format


def create_texture_mip_level(
    supercompression_scheme: SupercompressionScheme,
    level: RawTextureMipLevel,
    height: int,
    depth: int,
) -> gcftex.MipLevel:
    """Create an texture mip level from its description."""

    uncompressed_data: bytes = b""
    uncompressed_layer_size = -1

    for layer in level["layers"]:
        with open(layer, "rb") as layer_file:
            layer_data = layer_file.read()
            uncompressed_data += layer_data

            if uncompressed_layer_size < 0:
                uncompressed_layer_size = len(layer_data)
            elif not uncompressed_layer_size == len(layer_data):
                raise ValueError("Layers must all have the same size.")

    compressed_data = compress_data(uncompressed_data, supercompression_scheme)
    row_stride = level.get("row_stride", uncompressed_layer_size)
    depth_stride = level.get("depth_stride", row_stride * height)
    layer_stride = level.get("layer_stride", depth_stride * depth)

    descriptor = gcf_texture.MipLevelDescriptor(
        len(compressed_data), len(uncompressed_data), row_stride, depth_stride, layer_stride
    )

    return gcf_texture.MipLevel(descriptor, compressed_data)


def create_texture_resource(header: Header, raw: RawResource) -> Resource:
    """Create a texture resource from its raw description."""

    texture_resource = cast(RawTextureResource, raw)
    height = texture_resource.get("height", 1)
    depth = texture_resource.get("depth", 1)
    raw_mip_levels = texture_resource["mip_levels"]
    supercompression_scheme = deserialize_supercompression_scheme(texture_resource["supercompression_scheme"])

    mip_levels = tuple(
        map(
            lambda level_data: create_texture_mip_level(
                supercompression_scheme,
                level_data[1],
                round(max(1, height * 0.5 ** level_data[0])),
                round(max(1, depth * 0.5 ** level_data[0])),
            ),
            enumerate(raw_mip_levels),
        )
    )

    uncompressed_size = reduce(
        lambda a, b: sum((a, b)), map(lambda level: level.descriptor.uncompressed_size, mip_levels), 0
    )

    data_format = deserialize_format(texture_resource["format"])

    descriptor = gcf_texture.TextureResourceDescriptor(
        data_format,
        uncompressed_size,
        header=header,
        width=texture_resource["width"],
        height=height,
        depth=depth,
        layer_count=len(raw_mip_levels[0]["layers"]),
        mip_level_count=len(raw_mip_levels),
        supercompression_scheme=supercompression_scheme,
    )

    return gcf_texture.TextureResource(descriptor, mip_levels)


def create_blob_resource(header: Header, raw: RawResource) -> Resource:
    """Create a blob resource from its raw description."""

    blob_resource = cast(RawBlobResource, raw)
    supercompression_scheme = deserialize_supercompression_scheme(blob_resource["supercompression_scheme"])

    with open(blob_resource["file_path"], "rb") as blob_file:
        data = blob_file.read()

    uncompressed_size = len(data)
    compressed_data = compression.compress(data, supercompression_scheme.value)
    compressed_size = len(compressed_data)

    descriptor = gcf_blob.BlobResourceDescriptor(
        compressed_size,
        header=header,
        uncompressed_size=uncompressed_size,
        supercompression_scheme=supercompression_scheme,
    )

    return gcf_blob.BlobResource(descriptor, data)


def create_resource(header: Header, raw: RawResource) -> Resource:
    """Create a resource from its raw description."""

    res_type = get_resource_type(raw)

    if res_type == ResourceType.BLOB:
        return create_blob_resource(header, cast(RawBlobResource, raw))

    if res_type == ResourceType.TEXTURE:
        return create_texture_resource(header, cast(RawTextureResource, raw))

    raise ValueError("Unsupported resource type.", res_type)


def create_gcf_file(desc: RawGcfDescription) -> Tuple[Header, Iterable[Resource]]:
    """Create a GCF file from description.

    :param desc: The GCF file description.
    :return: A tuple containing the GCF header and the related sequence of resources.
    """

    header = create_header(desc)
    resources = []

    for resource_desc in desc["resources"]:
        resources.append(create_resource(header, resource_desc))

    return header, resources


def write_gcf_file(out_path: str, header: Header, resources: Iterable[Resource]):
    """Write a GCF file.

    This function will override an existing file.

    :param out_path: The path to the file that will be written.
    :param header: The GCF file header.
    :param resources: The ordered sequence of GCF resources to store in the file.
    """

    with open(out_path, "wb") as out_file:
        out_file.write(header.serialize())

        for res in resources:
            out_file.write(res.serialize())
