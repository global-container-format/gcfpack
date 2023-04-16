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


def test_validate_image_metadata_double_flag(raw_image_resource: meta.ImageResource):
    raw_image_resource["flags"] = ["image1d", "image1d"]

    with pytest.raises(ValueError):
        meta.validate_image_metadata(raw_image_resource)


def test_validate_image_metadata_too_many_image_flags(raw_image_resource: meta.ImageResource):
    raw_image_resource["flags"] = ["image1d", "image2d"]

    with pytest.raises(ValueError):
        meta.validate_image_metadata(raw_image_resource)
