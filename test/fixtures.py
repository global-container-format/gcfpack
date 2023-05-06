import os
import tempfile
import typing

import pytest

from gcfpack import meta


@pytest.fixture(scope="session")
def raw_container_flag_values():
    return typing.get_args(meta.GcfFlagValue)


@pytest.fixture(scope="session")
def raw_supercompression_scheme_values():
    literals = typing.get_args(meta.SuperCompressionScheme)

    return tuple(map(lambda lit: typing.get_args(lit)[0], literals))


@pytest.fixture()
def raw_blob_resource():
    return {"type": "blob", "file_path": "my-file.bin", "supercompression_scheme": "deflate"}


@pytest.fixture
def raw_texture_resource():
    return {
        "type": "texture",
        "base_width": 100,
        "base_height": 100,
        "flags": ["texture2d"],
        "supercompression_scheme": "none",
        "format": "R8_UNORM",
        "layer_count": 1,
        "texture_group": 0,
        "mip_levels": [
            {
                "row_stride": 10,
                "layers": ["only-layer.bin"],
            }
        ],
    }


@pytest.fixture
def gcf_description():
    return meta.create_sample_metadata_object()


@pytest.fixture(scope="session")
def tmp_texture_file():
    """A temporary raw texture data file.

    The create texture will be monochrome, one byte per pixel, white,
    w/size 1x1.
    """

    tmp = tempfile.NamedTemporaryFile("wb", delete=False)
    tmp.write(b"\xff")
    tmp.close()

    yield tmp.name

    os.unlink(tmp.name)


@pytest.fixture(scope="session")
def tmp_texture_file2():
    """A temporary raw texture data file.

    The create texture will be monochrome, one byte per pixel, white,
    w/size 2x1.
    """

    tmp = tempfile.NamedTemporaryFile("wb", delete=False)
    tmp.write(b"\xff\xff")
    tmp.close()

    yield tmp.name

    os.unlink(tmp.name)


@pytest.fixture
def tmp_texture_description(tmp_texture_file):
    return {
        "format": "R8_UNORM",
        "flags": ["texture2d"],
        "base_width": 1,
        "base_height": 1,
        "supercompression_scheme": "none",
        "layer_count": 1,
        "texture_group": 0,
        "type": "texture",
        "mip_levels": [{"row_stride": 1, "layers": [tmp_texture_file]}],
    }


@pytest.fixture
def tmp_blob_description(tmp_texture_file):
    return {"type": "blob", "file_path": tmp_texture_file, "supercompression_scheme": "none"}


@pytest.fixture
def empty_tmp_file():
    tmp = tempfile.NamedTemporaryFile("wb", delete=False)
    tmp.close()

    yield tmp.name

    os.unlink(tmp.name)


@pytest.fixture
def raw_texture_resource_no_format(raw_texture_resource):
    del raw_texture_resource["format"]

    return raw_texture_resource


@pytest.fixture
def raw_texture_resource_numeric_format(raw_texture_resource):
    raw_texture_resource["format"] = 8

    return raw_texture_resource


@pytest.fixture
def raw_texture_resource_empty_flags(raw_texture_resource):
    raw_texture_resource["flags"] = []

    return raw_texture_resource


@pytest.fixture
def raw_texture_resource_double_flag(raw_texture_resource):
    raw_texture_resource["flags"] = ["texture1d", "texture1d"]

    return raw_texture_resource


@pytest.fixture
def raw_texture_resource_too_many_flags(raw_texture_resource):
    raw_texture_resource["flags"] = ["texture1d", "texture2d"]

    return raw_texture_resource


@pytest.fixture
def raw_texture_resource_no_base_depth(raw_texture_resource):
    mip_level = raw_texture_resource["mip_levels"][0]
    raw_texture_resource["flags"] = ["texture3d"]
    mip_level["slice_stride"] = 5

    if "base_depth" in raw_texture_resource:
        del raw_texture_resource["base_depth"]

    return raw_texture_resource


@pytest.fixture
def raw_texture_resource_no_slice_stride(raw_texture_resource):
    mip_level = raw_texture_resource["mip_levels"][0]
    raw_texture_resource["flags"] = ["texture3d"]
    raw_texture_resource["base_depth"] = 5

    if "slice_stride" in mip_level:
        del mip_level["slice_stride"]

    return raw_texture_resource


@pytest.fixture
def raw_texture_resource_no_layer_stride(raw_texture_resource):
    mip_level = raw_texture_resource["mip_levels"][0]
    raw_texture_resource["flags"] = ["texture3d"]
    raw_texture_resource["base_depth"] = 5
    mip_level["layers"] = ["a", "b"]
    mip_level["slice_stride"] = 1

    if "layer_stride" in mip_level:
        del mip_level["layer_stride"]

    return raw_texture_resource


@pytest.fixture
def raw_texture_resource_no_row_stride(raw_texture_resource):
    mip_level = raw_texture_resource["mip_levels"][0]
    raw_texture_resource["flags"] = ["texture2d"]

    if "row_stride" in mip_level:
        del mip_level["row_stride"]

    return raw_texture_resource


@pytest.fixture
def raw_texture_resource_no_height(raw_texture_resource):
    raw_texture_resource["flags"] = ["texture2d"]

    if "base_height" in raw_texture_resource:
        del raw_texture_resource["base_height"]

    return raw_texture_resource


@pytest.fixture
def raw_texture_resource_1d_texture(raw_texture_resource):
    mip_level = raw_texture_resource["mip_levels"][0]
    raw_texture_resource["flags"] = ["texture1d"]

    for field in ("base_depth", "base_height"):
        if field in raw_texture_resource:
            del raw_texture_resource[field]  # type: ignore

    if "row_stride" in mip_level:
        del mip_level["row_stride"]

    return raw_texture_resource
