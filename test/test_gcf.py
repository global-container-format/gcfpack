from typing import cast

import pytest
from gcf import Header, ResourceType, SupercompressionScheme
from gcf.blob import BlobResource
from gcf.image import ImageResource

from gcfpack import gcf, meta

from .fixtures import (
    empty_tmp_file,
    gcf_description,
    raw_blob_resource,
    raw_container_flag_values,
    raw_image_resource,
    raw_supercompression_scheme_values,
    tmp_image_file,
    tmp_image_file_blob_description,
    tmp_image_file_image_description,
)


def test_deserialize_container_flags(raw_container_flag_values):
    """Test all valid flag values."""

    # Will except if not valid
    gcf.deserialize_container_flags(raw_container_flag_values)


def test_deserialize_container_flags_invalid():
    with pytest.raises(ValueError):
        gcf.deserialize_container_flags(["invalid"])


def test_deserialize_supercompression_scheme(raw_supercompression_scheme_values):
    for scheme in raw_supercompression_scheme_values:
        # Will except if not valid
        gcf.deserialize_supercompression_scheme(scheme)


def test_deserialize_supercompression_scheme_invalid():
    with pytest.raises(ValueError):
        gcf.deserialize_supercompression_scheme("invalid")


@pytest.mark.parametrize(
    "resource_name,resource_type",
    [(raw_blob_resource.__name__, ResourceType.BLOB), (raw_image_resource.__name__, ResourceType.IMAGE)],
)
def test_get_resource_type(resource_name, resource_type, request):
    resource = request.getfixturevalue(resource_name)

    assert gcf.get_resource_type(resource) == resource_type


def test_get_resource_type_invalid():
    with pytest.raises(ValueError):
        gcf.get_resource_type({"type": "invalid"})


def test_create_header(gcf_description):
    header = gcf.create_header(gcf_description)

    assert isinstance(header, Header)
    assert not header.is_gcf_file_unpadded
    assert header.resource_count == 2


def test_create_image_resource(tmp_image_file, tmp_image_file_image_description):
    description: meta.Metadata = {"header": {"version": 2}, "resources": [tmp_image_file_image_description]}

    header = gcf.create_header(description)
    result = gcf.create_image_resource(header, tmp_image_file_image_description)

    assert isinstance(result, ImageResource)

    image_result = cast(ImageResource, result)

    assert len(image_result.mip_levels) == 1
    assert image_result.descriptor.size == 1
    assert image_result.mip_levels[0].descriptor.compressed_size == 1
    assert image_result.mip_levels[0].descriptor.uncompressed_size == 1
    assert image_result.mip_levels[0].descriptor.row_stride == 1
    assert image_result.mip_levels[0].descriptor.depth_stride == 1
    assert image_result.mip_levels[0].descriptor.layer_stride == 1
    assert image_result.mip_levels[0].data == b"\xff"


def test_compress_data():
    for scheme in [SupercompressionScheme.NO_COMPRESSION, SupercompressionScheme.DEFLATE, SupercompressionScheme.ZLIB]:
        assert gcf.compress_data(b"asd", scheme)


def test_create_blob_resource(tmp_image_file, tmp_image_file_blob_description):
    description: meta.Metadata = {"header": {"version": 2}, "resources": [tmp_image_file_blob_description]}

    header = gcf.create_header(description)
    result = gcf.create_blob_resource(header, tmp_image_file_blob_description)

    assert isinstance(result, BlobResource)

    blob_result = cast(BlobResource, result)

    assert blob_result.descriptor.size == 1
    assert blob_result.content_data == b"\xff"
    assert blob_result.descriptor.size == 1


@pytest.mark.parametrize(
    "resource_type,resource_desc_name",
    [
        (BlobResource, tmp_image_file_blob_description.__name__),
        (ImageResource, tmp_image_file_image_description.__name__),
    ],
)
def test_create_resource(request, resource_type, resource_desc_name):
    resource_desc = request.getfixturevalue(resource_desc_name)

    description: meta.Metadata = {"header": {"version": 2}, "resources": [resource_desc]}

    header = gcf.create_header(description)

    assert isinstance(gcf.create_resource(header, resource_desc), resource_type)


def test_create_resource_invalid():
    resource_desc = {"type": "invalid"}

    description: meta.Metadata = {"header": {"version": 2}, "resources": [resource_desc]}

    header = gcf.create_header(description)

    with pytest.raises(ValueError):
        gcf.create_resource(header, resource_desc)


def test_create_gcf_file(tmp_image_file_image_description, tmp_image_file_blob_description):
    description: meta.Metadata = {
        "header": {"version": 2, "flags": ["unpadded"]},
        "resources": [tmp_image_file_blob_description, tmp_image_file_image_description],
    }

    header, resources = gcf.create_gcf_file(description)
    res_list = list(resources)

    assert header.resource_count == 2
    assert len(res_list) == 2
    assert isinstance(res_list[0], BlobResource)
    assert isinstance(res_list[1], ImageResource)


def test_write_gcf_file(empty_tmp_file, tmp_image_file_image_description, tmp_image_file_blob_description):
    description: meta.Metadata = {
        "header": {"version": 2, "flags": ["unpadded"]},
        "resources": [tmp_image_file_blob_description, tmp_image_file_image_description],
    }

    header, resources = gcf.create_gcf_file(description)

    gcf.write_gcf_file(empty_tmp_file, header, resources)

    with open(empty_tmp_file, "rb") as gcf_file:
        header = Header.from_file(gcf_file)

    assert header.version == 2
    assert header.resource_count == 2