import json
import sys
from os import unlink
from tempfile import NamedTemporaryFile
from typing import Tuple

import pytest

import gcfpack
from gcfpack.meta import Metadata


@pytest.fixture
def tmp_output_file():
    tmpfile = NamedTemporaryFile(delete=False)
    tmpfile.close()

    yield tmpfile.name

    unlink(tmpfile.name)


@pytest.fixture
def gcfpack_invoke_cmdline():
    return (sys.executable, f"-m{gcfpack.__package__}")


@pytest.fixture
def gcfpack_invoke_cmdline_w_options(gcfpack_invoke_cmdline, tmp_output_file):
    return gcfpack_invoke_cmdline + ("init", "-o", tmp_output_file)


@pytest.fixture(scope="session")
def mock_meta_file():
    tmpfile = NamedTemporaryFile("w", delete=False)
    blob_data_file = NamedTemporaryFile("wb", delete=False)

    blob_data_file.write(b"123")
    blob_data_file.close()

    meta: Metadata = {
        "header": {"version": 3},
        "resources": [{"type": "blob", "file_path": blob_data_file.name, "supercompression_scheme": "deflate"}],
    }

    json.dump(meta, tmpfile)
    tmpfile.close()

    yield tmpfile.name

    unlink(tmpfile.name)
    unlink(blob_data_file.name)


@pytest.fixture(scope="session")
def mock_bad_meta_file():
    tmpfile = NamedTemporaryFile("w", delete=False)
    blob_data_file = NamedTemporaryFile("wb", delete=False)

    blob_data_file.write(b"123")
    blob_data_file.close()

    meta: dict = {"header": {}}

    json.dump(meta, tmpfile)
    tmpfile.close()

    yield tmpfile.name

    unlink(tmpfile.name)
    unlink(blob_data_file.name)


@pytest.fixture
def gcfpack_invoke_cmdline_create(gcfpack_invoke_cmdline, mock_meta_file, tmp_output_file):
    return gcfpack_invoke_cmdline + ("create", "-i", mock_meta_file, "-o", tmp_output_file)


@pytest.fixture
def gcfpack_invoke_cmdline_create_dry_run(gcfpack_invoke_cmdline, mock_meta_file):
    return gcfpack_invoke_cmdline + ("create", "-i", mock_meta_file, "-n")


@pytest.fixture
def gcfpack_invoke_cmdline_create_dry_run_bad_metadata(gcfpack_invoke_cmdline, mock_bad_meta_file):
    return gcfpack_invoke_cmdline + ("create", "-i", mock_bad_meta_file, "-n")
