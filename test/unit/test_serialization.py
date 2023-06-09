from io import BytesIO

import pytest
from gcf import ContainerFlags, Format, ResourceType, blob, deserialize_header
from gcf import file as gcffile
from gcf import texture

from gcfpack import meta, serialization

from .conftest import raw_blob_resource, raw_texture_resource


def test_deserialize_container_flags(raw_container_flag_values):
    """Test all valid flag values."""

    # Will except if not valid
    serialization.deserialize_container_flags(raw_container_flag_values)


def test_deserialize_container_flags_invalid():
    with pytest.raises(ValueError):
        serialization.deserialize_container_flags(["invalid"])


def test_deserialize_supercompression_scheme(raw_supercompression_scheme_values):
    for scheme in raw_supercompression_scheme_values:
        # Will except if not valid
        serialization.deserialize_supercompression_scheme(scheme)


def test_deserialize_supercompression_scheme_invalid():
    with pytest.raises(ValueError):
        serialization.deserialize_supercompression_scheme("invalid")


@pytest.mark.parametrize(
    "resource_name,resource_type",
    [(raw_blob_resource.__name__, ResourceType.BLOB), (raw_texture_resource.__name__, ResourceType.TEXTURE)],
)
def test_get_resource_type(resource_name, resource_type, request):
    resource = request.getfixturevalue(resource_name)

    assert serialization.get_resource_type(resource) == resource_type


def test_get_resource_type_invalid():
    with pytest.raises(ValueError):
        serialization.get_resource_type({"type": "invalid"})


def test_create_header(gcf_description):
    raw_header = serialization.create_header(gcf_description)

    assert isinstance(raw_header, bytes)

    header = deserialize_header(raw_header)

    assert not ContainerFlags.UNPADDED in header["flags"]
    assert header["resource_count"] == 2


def test_create_header_no_flags(gcf_description_no_flags):
    raw_header = serialization.create_header(gcf_description_no_flags)

    assert isinstance(raw_header, bytes)

    # Must not raise because of missing flags field
    deserialize_header(raw_header)


def test_create_texture_resource(tmp_texture_description):
    raw_tex = serialization.create_texture_resource(tmp_texture_description)

    assert isinstance(raw_tex, bytes)

    tex_descriptor = texture.deserialize_texture_resource_descriptor(raw_tex[: texture.TOTAL_DESCRIPTOR_SIZE])
    tex_data = raw_tex[texture.TOTAL_DESCRIPTOR_SIZE :]
    mip_level_descriptor = texture.deserialize_mip_level_descriptor(tex_data[: texture.MIP_LEVEL_SIZE])
    mip_level_data = tex_data[texture.MIP_LEVEL_SIZE :]

    assert tex_descriptor["mip_level_count"] == 1
    assert tex_descriptor["content_size"] == 1 + texture.MIP_LEVEL_SIZE
    assert tex_descriptor["texture_group"] == 0
    assert tex_descriptor["layer_count"] == 1
    assert mip_level_descriptor["compressed_size"] == 1
    assert mip_level_descriptor["uncompressed_size"] == 1
    assert mip_level_descriptor["row_stride"] == 1
    assert mip_level_descriptor["slice_stride"] == 1
    assert mip_level_descriptor["layer_stride"] == 1
    assert mip_level_data == b"\xff"


def test_create_texture_resource_multiple_layers(tmp_texture_description_multiple_layers: meta.TextureResource):
    raw_tex = serialization.create_texture_resource(tmp_texture_description_multiple_layers)

    assert isinstance(raw_tex, bytes)

    tex_descriptor = texture.deserialize_texture_resource_descriptor(raw_tex[: texture.TOTAL_DESCRIPTOR_SIZE])
    tex_data = raw_tex[texture.TOTAL_DESCRIPTOR_SIZE :]
    mip_level_descriptor = texture.deserialize_mip_level_descriptor(tex_data[: texture.MIP_LEVEL_SIZE])
    mip_level_data = tex_data[texture.MIP_LEVEL_SIZE :]

    assert tex_descriptor["mip_level_count"] == 1
    assert tex_descriptor["content_size"] == 2 + texture.MIP_LEVEL_SIZE
    assert tex_descriptor["texture_group"] == 0
    assert tex_descriptor["layer_count"] == 2
    assert mip_level_descriptor["compressed_size"] == 2
    assert mip_level_descriptor["uncompressed_size"] == 2
    assert mip_level_descriptor["row_stride"] == 1
    assert mip_level_descriptor["slice_stride"] == 1
    assert mip_level_descriptor["layer_stride"] == 1
    assert mip_level_data == b"\xff\xff"


def test_create_texture_resource_invalid_layer_count(tmp_texture_description_invalid_layer_count):
    with pytest.raises(ValueError, match="Layer count"):
        serialization.create_texture_resource(tmp_texture_description_invalid_layer_count)


def test_create_texture_resource_multiple_layers_different_size(
    tmp_texture_description_multiple_layers_different_size: meta.TextureResource,
):
    with pytest.raises(ValueError):
        serialization.create_texture_resource(tmp_texture_description_multiple_layers_different_size)


def test_create_blob_resource(tmp_blob_description):
    raw_blob = serialization.create_blob_resource(tmp_blob_description)

    assert isinstance(raw_blob, bytes)

    descriptor = blob.deserialize_blob_descriptor(raw_blob[: blob.TOTAL_DESCRIPTOR_SIZE])
    data = raw_blob[blob.TOTAL_DESCRIPTOR_SIZE :]

    assert descriptor["content_size"] == 1
    assert descriptor["uncompressed_size"] == 1
    assert data == b"\xff"


def test_create_gcf_file(tmp_blob_and_texture_metadata: meta.Metadata):
    raw_gcf = serialization.create_gcf_file(tmp_blob_and_texture_metadata)
    test_file = BytesIO(raw_gcf)
    header = gcffile.read_header(test_file)
    res_list = []

    assert header["resource_count"] == 2

    for _ in range(header["resource_count"]):
        descriptor = gcffile.read_common_resource_descriptor(test_file)
        res_list.append(descriptor)

    assert len(res_list) == 2
    assert res_list[0]["type"] == ResourceType.BLOB.value
    assert res_list[1]["type"] == ResourceType.TEXTURE.value


def test_deserialize_format_numeric():
    assert serialization.deserialize_format(123) == 123


def test_deserialize_format_enum():
    assert serialization.deserialize_format(Format.E5B9G9R9_UFLOAT_PACK32) == 123


def test_deserialize_texture_flags(valid_texture_flags, invalid_texture_flags):
    # Will throw if invalid
    serialization.deserialize_texture_flags(valid_texture_flags)

    with pytest.raises(ValueError):
        serialization.deserialize_texture_flags(invalid_texture_flags)
