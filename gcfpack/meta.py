"""Metadata file management.

This module contains all the code to load, store and validate
GCF metadata (aka description) files.
"""

import json
from typing import Any, List, Literal, NotRequired, TextIO, TypedDict, Union, cast

GcfFlagValue = Literal["unpadded"]
ImageFlagValue = Union[Literal["image1d"], Literal["image2d"], Literal["image3d"]]
SuperCompressionScheme = Union[Literal["zlib"], Literal["deflate"], Literal["none"], Literal["test"]]


class Header(TypedDict):
    """GCF header representation."""

    version: Literal[2]
    flags: NotRequired[List[GcfFlagValue]]


class BaseResource(TypedDict):
    """The base class for all resources in a description object."""

    format: int
    super_compression_scheme: SuperCompressionScheme


class BlobResource(BaseResource):
    """A blob resource representation."""

    type: Literal["blob"]
    file_path: str


class ImageMipLevel(TypedDict):
    """An image mip level representation."""

    row_stride: int
    depth_stride: int
    layer_stride: int
    layers: List[str]


class ImageResource(BaseResource):
    """An image resource representation."""

    type: Literal["image"]
    width: int
    height: int
    depth: int
    flags: List[ImageFlagValue]
    mip_levels: List[ImageMipLevel]


Resource = Union[BlobResource, ImageResource]


class Metadata(TypedDict):
    """A GCF description object."""

    header: Header
    resources: List[Resource]


def create_sample_metadata_object() -> Metadata:
    """Create an example description object.

    :return: An example description object to simplify manual description creation.
    """

    blob_resource_example = cast(BlobResource, {"type": "blob", "file_path": "my-file.bin"})

    image_resource_example = cast(
        ImageResource,
        {
            "type": "image",
            "width": 100,
            "height": 100,
            "depth": 1,
            "flags": ["image2d"],
            "mip_levels": [
                {
                    "row_stride": 10,
                    "depth_stride": 200,
                    "layer_stride": 200,
                    "layers": ["only-layer.bin"],
                }
            ],
        },
    )

    return {
        "header": {"version": 2, "flags": []},
        "resources": [blob_resource_example, image_resource_example],
    }


def store_metadata(out_file: TextIO, meta: Metadata):
    """Store a description object to file.

    :param out_file: The output file.
    :param meta: The description object to store.
    """

    json.dump(meta, out_file, indent=4)


def validate_metadata(meta: Any):
    """Validate a description object.

    This function will raise a `ValueError` if the provided
    object is not a valid description object.

        :param meta: The description object to validate.
    """

    return True


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
