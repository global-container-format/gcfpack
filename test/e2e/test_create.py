from subprocess import PIPE, CalledProcessError, check_call, check_output

import pytest
from gcf.file import read_header


def test_create(gcfpack_invoke_cmdline_create):
    output_file = gcfpack_invoke_cmdline_create[-1]

    check_call(gcfpack_invoke_cmdline_create)

    # Will raise if not a valid GCF file
    with open(output_file, "rb") as f:
        read_header(f)


def test_create_dry_run(gcfpack_invoke_cmdline_create_dry_run):
    # Will raise if not a valid description file
    check_call(gcfpack_invoke_cmdline_create_dry_run)


def test_create_dry_run_bad_metadata(gcfpack_invoke_cmdline_create_dry_run_bad_metadata):
    try:
        check_output(gcfpack_invoke_cmdline_create_dry_run_bad_metadata, stderr=PIPE)
        pytest.fail("Did not throw.")
    except CalledProcessError as exc:
        err_output = exc.stderr.decode("utf-8")

        assert "Invalid description file" in err_output
