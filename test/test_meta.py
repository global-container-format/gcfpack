import io
import json

import pydantic
import pytest

from gcfpack import meta


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


def test_load_metadata_valid():
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


def test_validate_metadata_valid():
    sample_meta = meta.create_sample_metadata_object()

    # No exception upon success
    meta.validate_metadata(sample_meta)


def test_validate_metadata_invalid():
    with pytest.raises(ValueError):
        meta.validate_metadata({})
