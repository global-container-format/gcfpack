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
def tmp_texture_file_texture_description(tmp_texture_file):
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
def tmp_texture_file_blob_description(tmp_texture_file):
    return {"type": "blob", "file_path": tmp_texture_file, "supercompression_scheme": "none"}


@pytest.fixture
def empty_tmp_file():
    tmp = tempfile.NamedTemporaryFile("wb", delete=False)
    tmp.close()

    yield tmp.name

    os.unlink(tmp.name)
