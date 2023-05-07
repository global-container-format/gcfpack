"""Metadata file management.

This module contains all the code to load, store and validate
GCF metadata (aka description) files.
"""

import json
from functools import reduce
from typing import Any, Literal, NotRequired, TextIO, TypedDict, Union, cast

import pydantic

GcfFlagValue = Literal["unpadded"]
TextureFlagValue = Union[Literal["texture1d"], Literal["texture2d"], Literal["texture3d"]]
SuperCompressionScheme = Union[Literal["zlib"], Literal["deflate"], Literal["none"], Literal["test"]]


class Header(TypedDict):
    """GCF header representation."""

    version: Literal[3]
    flags: NotRequired[list[GcfFlagValue]]


class BaseResource(TypedDict):
    """The base class for all resources in a description object."""

    format: NotRequired[Union[str, int]]
    supercompression_scheme: SuperCompressionScheme


class BlobResource(BaseResource):
    """A blob resource representation."""

    type: Literal["blob"]
    file_path: str


class TextureMipLevel(TypedDict):
    """An texture mip level representation."""

    row_stride: NotRequired[int]
    slice_stride: NotRequired[int]
    layer_stride: NotRequired[int]
    layers: list[str]


class TextureResource(BaseResource):
    """An texture resource representation."""

    type: Literal["texture"]
    base_width: int
    base_height: NotRequired[int]
    base_depth: NotRequired[int]
    layer_count: int
    flags: list[TextureFlagValue]
    mip_levels: list[TextureMipLevel]
    texture_group: int


Resource = Union[BlobResource, TextureResource]


class Metadata(TypedDict):
    """A GCF description object."""

    header: Header
    resources: list[Resource]


def create_sample_metadata_object() -> Metadata:
    """Create an example description object.

    :return: An example description object to simplify manual description creation.
    """

    blob_resource_example: BlobResource = {
        "type": "blob",
        "file_path": "my-file.bin",
        "supercompression_scheme": "deflate",
    }

    tex_resource_example: TextureResource = {
        "type": "texture",
        "format": "R8_UNORM",
        "base_width": 100,
        "base_height": 100,
        "flags": ["texture2d"],
        "supercompression_scheme": "none",
        "layer_count": 1,
        "texture_group": 0,
        "mip_levels": [
            {
                "row_stride": 10,
                "layers": ["only-layer.bin"],
            }
        ],
    }

    return {
        "header": {"version": 3, "flags": []},
        "resources": [blob_resource_example, tex_resource_example],
    }


def store_metadata(out_file: TextIO, meta: Metadata):
    """Store a description object to file.

    :param out_file: The output file.
    :param meta: The description object to store.
    """

    json.dump(meta, out_file, indent=4)


def validate_texture_metadata(res: TextureResource):
    """Validate texture metadata.

    The metadata is assumed to be already matching
    the general resource structure.

    This function will raise a `ValueError` if the provided
    description object is not a valid texture resource.
    """

    texture_types = ("texture1d", "texture2d", "texture3d")
    res_texture_type_count = reduce(lambda total, flag: total + int(flag in texture_types), res["flags"], 0)

    if res_texture_type_count != 1:
        raise ValueError(
            f"Texture resources must have exactly one texture dimension flag. Found {res_texture_type_count}.", res
        )

    if not "format" in res:
        raise ValueError("Texture resources must have an associated format.", res)

    if "texture1d" not in res["flags"]:
        if not "base_height" in res:
            raise ValueError("2D and 3D texture resources require base height to be specified.", res)

        for mip in res["mip_levels"]:
            if not "row_stride" in mip:
                raise ValueError("2D and 3D texture resources require row stride to be specified.", res)

    if "texture3d" in res["flags"]:
        if not "base_depth" in res:
            raise ValueError("3D texture resources require base depth to be specified.", res)

        for mip in res["mip_levels"]:
            if not "slice_stride" in mip:
                raise ValueError("3D texture resources require slice stride to be specified.", res)

    for mip in res["mip_levels"]:
        if len(mip["layers"]) > 1 and not "layer_stride" in mip:
            raise ValueError("Multi-layer texture resources require layer stride to be specified.", res)


def validate_metadata(maybe_meta: Any):
    """Validate a description object.

    This function will raise a `ValueError` if the provided
    object is not a valid description object.

    :param meta: The description object to validate.
    """
    meta_model = pydantic.create_model_from_typeddict(Metadata)
    validation_errors = pydantic.validate_model(meta_model, maybe_meta)[2]  # pylint: disable=no-member

    if validation_errors:
        raise ValueError("Invalid GCF description.", validation_errors)

    meta = cast(Metadata, maybe_meta)

    for res in meta["resources"]:
        if res["type"] == "texture":
            validate_texture_metadata(res)


def load_metadata(description_file: TextIO) -> Metadata:
    """Load a description file.

    This function will raise an `IOError` if the provided file
    is not a valid description file.

    :param description_file: The description file.

    :return: The loaded description object.
    """

    try:
        meta = json.load(description_file)
        validate_metadata(meta)
    except Exception as exc:
        raise IOError("Invalid description file.") from exc

    return cast(Metadata, meta)
