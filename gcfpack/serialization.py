"""GCF file packaging."""

from typing import Callable, Dict, Iterable, List, Union, cast

from gcf import ContainerFlags, Format, Header, ResourceType, SupercompressionScheme
from gcf import blob as gcfblob
from gcf import compression
from gcf import header as gcfheader
from gcf import make_blob_resource_descriptor
from gcf import texture as gcftex
from gcf import util as gcfutil

from .meta import BlobResource as RawBlobResource
from .meta import Metadata as RawGcfDescription
from .meta import Resource as RawResource
from .meta import TextureMipLevel as RawTextureMipLevel
from .meta import TextureResource as RawTextureResource

CreateResourceFunction = Callable[[RawResource], bytes]


def deserialize_container_flags(raw: Iterable[str]) -> ContainerFlags:
    """Deserialize a sequence of container flags."""

    result: ContainerFlags = ContainerFlags(0)

    for flag in raw:
        if flag == "unpadded":
            result |= ContainerFlags.UNPADDED
        else:
            raise ValueError("Invalid container flag.", flag)

    return result


def deserialize_texture_flags(raw: Iterable[str]) -> gcftex.TextureFlags:
    """Deserialize a sequence of texture flags."""

    result: gcftex.TextureFlags = gcftex.TextureFlags(0)

    flag_map: Dict[str, gcftex.TextureFlags] = {
        "texture1d": gcftex.TextureFlags.TEXTURE_1D,
        "texture2d": gcftex.TextureFlags.TEXTURE_2D,
        "texture3d": gcftex.TextureFlags.TEXTURE_3D,
    }

    try:
        for flag in raw:
            result |= flag_map[flag]
    except KeyError as exc:
        raise ValueError("Invalid container flag.", flag) from exc

    return result


def deserialize_supercompression_scheme(raw: str) -> SupercompressionScheme:
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


def get_resource_type(res: Union[RawResource, dict]) -> ResourceType:
    """Get the resource type from a raw resource."""

    res_type = res["type"]

    if res_type == "blob":
        return ResourceType.BLOB

    if res_type == "texture":
        return ResourceType.TEXTURE

    raise ValueError("Invalid resource type.", res_type)


def deserialize_format(raw_format: Union[str, int]) -> int:
    """Deserialize a raw format representation into a numeric format value."""

    if isinstance(raw_format, str):
        return Format[raw_format].value

    return raw_format


def create_header(desc: RawGcfDescription) -> bytes:
    """Create a GCF file header from its raw description."""

    version = gcfheader.make_magic_number()
    flags = deserialize_container_flags(desc["header"].get("flags", []))
    header: Header = {"magic": version, "flags": flags, "resource_count": len(desc["resources"])}

    return gcfheader.serialize_header(header)


def create_blob_resource(raw: RawResource) -> bytes:
    """Create a GCF blob resource from its raw description."""

    blob_resource = cast(RawBlobResource, raw)
    file_path = blob_resource["file_path"]

    supercompression_scheme = deserialize_supercompression_scheme(blob_resource["supercompression_scheme"])

    with open(file_path, "rb") as content_file:
        content = content_file.read()

    compressed_content = compression.compress(content, supercompression_scheme)
    descriptor = make_blob_resource_descriptor(len(compressed_content), len(content), supercompression_scheme)

    return gcfblob.serialize_blob_descriptor(descriptor) + compressed_content


def create_texture_resource(raw: RawResource) -> bytes:
    """Create a GCF texture resource from its raw description."""

    tex_resource = cast(RawTextureResource, raw)
    format_ = deserialize_format(tex_resource["format"])
    supercompression_scheme = deserialize_supercompression_scheme(tex_resource["supercompression_scheme"])
    base_width = tex_resource["base_width"]
    base_height = tex_resource.get("base_height", 1)
    base_depth = tex_resource.get("base_depth", 1)
    layer_count = tex_resource["layer_count"]
    texture_group = tex_resource["texture_group"]
    flags = deserialize_texture_flags(tex_resource["flags"])
    level_collection: List[bytes] = []

    for level_index, level in enumerate(tex_resource["mip_levels"]):
        level_collection.append(create_texture_mip_level(tex_resource, level, level_index))

    data = b"".join(level_collection)

    descriptor = gcftex.make_texture_resource_descriptor(
        format_=format_,
        content_size=len(data),
        supercompression_scheme=supercompression_scheme,
        base_width=base_width,
        base_height=base_height,
        base_depth=base_depth,
        mip_level_count=len(level_collection),
        layer_count=layer_count,
        texture_group=texture_group,
        flags=flags,
    )

    return gcftex.serialize_texture_resource_descriptor(descriptor) + data


# pylint: disable=too-many-locals
def create_texture_mip_level(tex_resource: RawTextureResource, level: RawTextureMipLevel, level_index: int) -> bytes:
    """Create a GCF texture mip level from its raw description."""

    supercompression_scheme = deserialize_supercompression_scheme(tex_resource["supercompression_scheme"])
    expected_layer_count = tex_resource["layer_count"]
    actual_layer_count = len(level["layers"])
    layer_collection: List[bytes] = []

    if expected_layer_count != actual_layer_count:
        raise ValueError(f"Layer count is {expected_layer_count} but mip level has {actual_layer_count} layers.")

    for layer in level["layers"]:
        with open(layer, "rb") as layer_file:
            layer_collection.append(layer_file.read())

    for layer_index, layer_data in enumerate(layer_collection[1:]):
        if len(layer_data) != len(layer_collection[0]):
            raise ValueError(f"Layer {layer_index} in texture mip_level {level_index} has different size.")

    uncompressed_data_size = sum(map(len, layer_collection))
    data = gcftex.serialize_mip_level_data(layer_collection, supercompression_scheme)

    base_width = tex_resource["base_width"]
    base_height = tex_resource.get("base_height", 1)
    base_depth = tex_resource.get("base_depth", 1)

    level_width, level_height, level_depth = gcfutil.compute_mip_level_size(
        level_index, base_width, base_height, base_depth
    )
    slice_stride = level_width * level_height
    layer_stride = slice_stride * level_depth

    descriptor: gcftex.MipLevelDescriptor = {
        "compressed_size": len(data),
        "uncompressed_size": uncompressed_data_size,
        "row_stride": level.get("row_stride", level_width),
        "slice_stride": level.get("slice_stride", slice_stride),
        "layer_stride": level.get("layer_stride", layer_stride),
    }

    return gcftex.serialize_mip_level_descriptor(descriptor) + data


def create_gcf_file(description: RawGcfDescription) -> bytes:
    """Create a GCF file from its raw description."""

    raw_resource_collection = description["resources"]
    resource_data_collection = []

    resource_create_map: Dict[ResourceType, CreateResourceFunction] = {
        ResourceType.BLOB: create_blob_resource,
        ResourceType.TEXTURE: create_texture_resource,
    }

    for raw_resource in raw_resource_collection:
        resource_type = get_resource_type(raw_resource)
        create_resource = resource_create_map[resource_type]

        resource_data_collection.append(create_resource(raw_resource))

    return create_header(description) + b"".join(resource_data_collection)
