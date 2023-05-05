"""GCF file packaging."""

from functools import reduce
from typing import Iterable, Tuple, Union, cast

from gcf import ContainerFlags, Header, ResourceType, SupercompressionScheme, Format, make_blob_resource_descriptor
from gcf import header as gcfheader
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


def deserialize_format(raw_format: Union[str, int]) -> int:
    """Deserialize a raw format representation into a numeric format value."""

    if isinstance(raw_format, str):
        return Format[raw_format].value

    return raw_format


def create_header(desc: RawGcfDescription) -> bytes:
    version = gcfheader.make_magic_number()
    flags = deserialize_container_flags(desc["header"]["flags"])
    header: Header = {
        "version": version,
        "flags": flags,
        "resource_count": len(desc["resources"])
    }

    return gcfheader.serialize_header(header)


def create_blob_resource(header: Header, raw: RawResource) -> bytes:
    blob_resource = cast(RawBlobResource, raw)
    file_path = blob_resource["file_path"]

    format = deserialize_format(
        blob_resource["format"]
    )

    supercompression_scheme = deserialize_supercompression_scheme(
        blob_resource["supercompression_scheme"]
    )

    with open(file_path, "rb") as f:
        content = f.read()

    compressed_content = compression.compress(content, supercompression_scheme)
    descriptor = make_blob_resource_descriptor(len(compressed_content), len(content), supercompression_scheme)

    return gcfblob.serialize_blob_descriptor(descriptor) + compressed_content
