import io
import json

import pydantic
import pytest

from gcfpack import meta

from .fixtures import raw_image_resource


def test_create_sample_metadata_object():
    """Test result shape."""

    model = pydantic.create_model_from_typeddict(meta.Metadata)
    sample_meta = meta.create_sample_metadata_object()
    validation_errors = pydantic.validate_model(model, sample_meta)[2]

    assert not validation_errors


def test_store_metadatata():
    """Test `store_metadata()` stores a JSON GCF description."""

    sample_meta = meta.create_sample_metadata_object()
    test_file = io.StringIO()

    meta.store_metadata(test_file, sample_meta)

    assert json.loads(test_file.getvalue()) == sample_meta


def test_load_metadata():
    """Ensure `load_metadata()` loads a valid file."""

    sample_meta = meta.create_sample_metadata_object()
    test_file = io.StringIO()

    meta.store_metadata(test_file, sample_meta)
    test_file.seek(0)

    assert meta.load_metadata(test_file) == sample_meta


def test_load_metadata_invalid():
    """Ensure `load_metadata()` doesn't load an invalid file."""

    test_file = io.StringIO("{}")

    with pytest.raises(IOError):
        meta.load_metadata(test_file)


def test_validate_metadata():
    sample_meta = meta.create_sample_metadata_object()

    # No exception upon success
    meta.validate_metadata(sample_meta)


def test_validate_metadata_invalid():
    with pytest.raises(ValueError):
        meta.validate_metadata({})


def test_validate_image_metadata(raw_image_resource: meta.ImageResource):
    # No exception upon success
    meta.validate_image_metadata(raw_image_resource)


def test_validate_image_metadata_no_format(raw_image_resource: meta.ImageResource):
    del raw_image_resource["format"]

    with pytest.raises(ValueError):
        meta.validate_image_metadata(raw_image_resource)


def test_validate_image_metadata_empty_flags(raw_image_resource: meta.ImageResource):
    raw_image_resource["flags"] = []

    with pytest.raises(ValueError):
        meta.validate_image_metadata(raw_image_resource)


def test_validate_image_metadata_numeric_format(raw_image_resource: meta.ImageResource):
    raw_image_resource["format"] = 8

    # No exception upon success
    meta.validate_image_metadata(raw_image_resource)


def test_validate_image_metadata_double_flag(raw_image_resource: meta.ImageResource):
    raw_image_resource["flags"] = ["image1d", "image1d"]

    with pytest.raises(ValueError):
        meta.validate_image_metadata(raw_image_resource)


def test_validate_image_metadata_too_many_image_flags(raw_image_resource: meta.ImageResource):
    raw_image_resource["flags"] = ["image1d", "image2d"]

    with pytest.raises(ValueError):
        meta.validate_image_metadata(raw_image_resource)


def test_validate_image_metadata_no_depth(raw_image_resource: meta.ImageResource):
    mip_level = raw_image_resource["mip_levels"][0]
    raw_image_resource["flags"] = ["image3d"]
    mip_level["depth_stride"] = 5

    if "depth" in raw_image_resource:
        del raw_image_resource["depth"]

    with pytest.raises(ValueError):
        meta.validate_image_metadata(raw_image_resource)


def test_validate_image_metadata_no_depth_stride(raw_image_resource: meta.ImageResource):
    mip_level = raw_image_resource["mip_levels"][0]
    raw_image_resource["flags"] = ["image3d"]
    raw_image_resource["depth"] = 5

    if "depth_stride" in mip_level:
        del mip_level["depth_stride"]

    with pytest.raises(ValueError):
        meta.validate_image_metadata(raw_image_resource)


def test_validate_image_metadata_no_layer_stride(raw_image_resource: meta.ImageResource):
    mip_level = raw_image_resource["mip_levels"][0]
    raw_image_resource["flags"] = ["image3d"]
    mip_level["layers"] = ["a", "b"]

    if "layer_stride" in mip_level:
        del mip_level["layer_stride"]

    with pytest.raises(ValueError):
        meta.validate_image_metadata(raw_image_resource)


def test_validate_image_metadata_no_row_stride(raw_image_resource: meta.ImageResource):
    mip_level = raw_image_resource["mip_levels"][0]
    raw_image_resource["flags"] = ["image2d"]

    if "row_stride" in mip_level:
        del mip_level["row_stride"]

    with pytest.raises(ValueError):
        meta.validate_image_metadata(raw_image_resource)


def test_validate_image_metadata_no_height(raw_image_resource: meta.ImageResource):
    raw_image_resource["flags"] = ["image2d"]

    if "height" in raw_image_resource:
        del raw_image_resource["height"]

    with pytest.raises(ValueError):
        meta.validate_image_metadata(raw_image_resource)


def test_validate_image_metadata_1d_image(raw_image_resource: meta.ImageResource):
    mip_level = raw_image_resource["mip_levels"][0]
    raw_image_resource["flags"] = ["image1d"]

    for field in ("depth", "height"):
        if field in raw_image_resource:
            del raw_image_resource[field]

    if "row_stride" in mip_level:
        del mip_level["row_stride"]

    meta.validate_image_metadata(raw_image_resource)
