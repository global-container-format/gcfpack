import io
import json
from typing import Any, Dict, cast

import pydantic
import pytest

from gcfpack import meta

from .fixtures import raw_texture_resource


def test_create_sample_metadata_object():
    """Test result shape."""

    model = pydantic.create_model_from_typeddict(meta.Metadata)
    sample_meta = meta.create_sample_metadata_object()
    validation_errors = pydantic.validate_model(model, cast(Dict[str, Any], sample_meta))[2]

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


def test_validate_texture_metadata(raw_texture_resource: meta.TextureResource):
    # No exception upon success
    meta.validate_texture_metadata(raw_texture_resource)


def test_validate_texture_metadata_no_format(raw_texture_resource: meta.TextureResource):
    del raw_texture_resource["format"]

    with pytest.raises(ValueError):
        meta.validate_texture_metadata(raw_texture_resource)


def test_validate_texture_metadata_empty_flags(raw_texture_resource: meta.TextureResource):
    raw_texture_resource["flags"] = []

    with pytest.raises(ValueError):
        meta.validate_texture_metadata(raw_texture_resource)


def test_validate_texture_metadata_numeric_format(raw_texture_resource: meta.TextureResource):
    raw_texture_resource["format"] = 8

    # No exception upon success
    meta.validate_texture_metadata(raw_texture_resource)


def test_validate_texture_metadata_double_flag(raw_texture_resource: meta.TextureResource):
    raw_texture_resource["flags"] = ["texture1d", "texture1d"]

    with pytest.raises(ValueError):
        meta.validate_texture_metadata(raw_texture_resource)


def test_validate_texture_metadata_too_many_texture_flags(raw_texture_resource: meta.TextureResource):
    raw_texture_resource["flags"] = ["texture1d", "texture2d"]

    with pytest.raises(ValueError):
        meta.validate_texture_metadata(raw_texture_resource)


def test_validate_texture_metadata_no_base_depth(raw_texture_resource: meta.TextureResource):
    mip_level = raw_texture_resource["mip_levels"][0]
    raw_texture_resource["flags"] = ["texture3d"]
    mip_level["slice_stride"] = 5

    if "base_depth" in raw_texture_resource:
        del raw_texture_resource["base_depth"]

    with pytest.raises(ValueError, match="base depth"):
        meta.validate_texture_metadata(raw_texture_resource)


def test_validate_texture_metadata_no_slice_stride(raw_texture_resource: meta.TextureResource):
    mip_level = raw_texture_resource["mip_levels"][0]
    raw_texture_resource["flags"] = ["texture3d"]
    raw_texture_resource["base_depth"] = 5

    if "slice_stride" in mip_level:
        del mip_level["slice_stride"]

    with pytest.raises(ValueError, match="slice stride"):
        meta.validate_texture_metadata(raw_texture_resource)


def test_validate_texture_metadata_no_layer_stride(raw_texture_resource: meta.TextureResource):
    mip_level = raw_texture_resource["mip_levels"][0]
    raw_texture_resource["flags"] = ["texture3d"]
    raw_texture_resource["base_depth"] = 5
    mip_level["layers"] = ["a", "b"]
    mip_level["slice_stride"] = 1

    if "layer_stride" in mip_level:
        del mip_level["layer_stride"]

    with pytest.raises(ValueError, match="layer stride"):
        meta.validate_texture_metadata(raw_texture_resource)


def test_validate_texture_metadata_no_row_stride(raw_texture_resource: meta.TextureResource):
    mip_level = raw_texture_resource["mip_levels"][0]
    raw_texture_resource["flags"] = ["texture2d"]

    if "row_stride" in mip_level:
        del mip_level["row_stride"]

    with pytest.raises(ValueError, match="row stride"):
        meta.validate_texture_metadata(raw_texture_resource)


def test_validate_texture_metadata_no_height(raw_texture_resource: meta.TextureResource):
    raw_texture_resource["flags"] = ["texture2d"]

    if "base_height" in raw_texture_resource:
        del raw_texture_resource["base_height"]

    with pytest.raises(ValueError, match="base height"):
        meta.validate_texture_metadata(raw_texture_resource)


def test_validate_texture_metadata_1d_texture(raw_texture_resource: meta.TextureResource):
    mip_level = raw_texture_resource["mip_levels"][0]
    raw_texture_resource["flags"] = ["texture1d"]

    for field in ("base_depth", "base_height"):
        if field in raw_texture_resource:
            del raw_texture_resource[field]  # type: ignore

    if "row_stride" in mip_level:
        del mip_level["row_stride"]

    meta.validate_texture_metadata(raw_texture_resource)
