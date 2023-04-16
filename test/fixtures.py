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
def raw_image_resource():
    return {
        "type": "image",
        "width": 100,
        "height": 100,
        "depth": 1,
        "flags": ["image2d"],
        "supercompression_scheme": "none",
        "format": 9,
        "mip_levels": [
            {
                "row_stride": 10,
                "depth_stride": 200,
                "layer_stride": 200,
                "layers": ["only-layer.bin"],
            }
        ],
    }


@pytest.fixture
def gcf_description():
    return meta.create_sample_metadata_object()


@pytest.fixture(scope="session")
def tmp_image_file():
    """A temporary raw image data file.

    The create image will be monochrome, one byte per pixel, white,
    w/size 1x1.
    """

    tmp = tempfile.NamedTemporaryFile("wb", delete=False)
    tmp.write(b"\xff")
    tmp.close()

    yield tmp.name

    os.unlink(tmp.name)


@pytest.fixture
def tmp_image_file_image_description(tmp_image_file):
    return {
        "format": 9,
        "flags": ["image2d"],
        "width": 1,
        "height": 1,
        "depth": 1,
        "supercompression_scheme": "none",
        "type": "image",
        "mip_levels": [{"row_stride": 1, "depth_stride": 1, "layer_stride": 1, "layers": [tmp_image_file]}],
    }


@pytest.fixture
def tmp_image_file_blob_description(tmp_image_file):
    return {"type": "blob", "file_path": tmp_image_file, "supercompression_scheme": "none"}


@pytest.fixture
def empty_tmp_file():
    tmp = tempfile.NamedTemporaryFile("wb", delete=False)
    tmp.close()

    yield tmp.name

    os.unlink(tmp.name)
