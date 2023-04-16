"""GCF file packaging."""

from functools import reduce
from typing import Iterable, Tuple, cast

from gcf import ContainerFlags, Header, Resource, ResourceType, SupercompressionScheme, VkFormat
from gcf import blob as gcf_blob
from gcf import compress
from gcf import image as gcf_image

from .meta import BlobResource as RawBlobResource
from .meta import GcfFlagValue as RawContainerFlags
from .meta import ImageMipLevel as RawImageMipLevel
from .meta import ImageResource as RawImageResource
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

    if res_type == "image":
        return ResourceType.IMAGE

    raise ValueError("Invalid resource type.", res_type)


def create_header(desc: RawGcfDescription) -> Header:
    """Create a GCF header from its raw description."""

    raw_header = desc["header"]
    gcf_version = raw_header["version"]

    return Header(len(desc["resources"]), deserialize_container_flags(desc["header"].get("flags", [])), gcf_version)


def create_image_mip_level(
    supercompression_scheme: SupercompressionScheme,
    level: RawImageMipLevel,
) -> gcf_image.MipLevel:
    """Create an image mip level from its description."""

    uncompressed_data: bytes = b""

    for layer in level["layers"]:
        with open(layer, "rb") as layer_file:
            uncompressed_data += layer_file.read()

    compressed_data = compress_data(uncompressed_data, supercompression_scheme)

    descriptor = gcf_image.MipLevelDescriptor(
        len(compressed_data), len(uncompressed_data), level["row_stride"], level["depth_stride"], level["layer_stride"]
    )

    return gcf_image.MipLevel(descriptor, compressed_data)


def create_image_resource(header: Header, raw: RawResource) -> Resource:
    """Create a image resource from its raw description."""

    image_resource = cast(RawImageResource, raw)
    raw_mip_levels = image_resource["mip_levels"]
    supercompression_scheme = deserialize_supercompression_scheme(image_resource["supercompression_scheme"])

    mip_levels = tuple(map(lambda level: create_image_mip_level(supercompression_scheme, level), raw_mip_levels))

    uncompressed_size = reduce(
        lambda a, b: sum((a, b)), map(lambda level: level.descriptor.uncompressed_size, mip_levels), 0
    )

    descriptor = gcf_image.ImageResourceDescriptor(
        VkFormat(image_resource["format"]),
        uncompressed_size,
        header=header,
        width=image_resource["width"],
        height=image_resource["height"],
        depth=image_resource["depth"],
        layer_count=len(raw_mip_levels[0]["layers"]),
        mip_level_count=len(raw_mip_levels),
        supercompression_scheme=supercompression_scheme,
    )

    return gcf_image.ImageResource(descriptor, mip_levels)


def compress_data(data: bytes, scheme: SupercompressionScheme) -> bytes:
    """Compress GCF data with one of the supported schemes."""

    compressor = compress.COMPRESSOR_TABLE[scheme][0]

    return compressor(data)


def create_blob_resource(header: Header, raw: RawResource) -> Resource:
    """Create a blob resource from its raw description."""

    blob_resource = cast(RawBlobResource, raw)
    supercompression_scheme = deserialize_supercompression_scheme(blob_resource["supercompression_scheme"])

    with open(blob_resource["file_path"], "rb") as blob_file:
        data = blob_file.read()

    uncompressed_size = len(data)
    compressed_data = compress_data(data, supercompression_scheme)
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

    if res_type == ResourceType.IMAGE:
        return create_image_resource(header, cast(RawImageResource, raw))

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
