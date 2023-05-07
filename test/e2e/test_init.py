"""Tests for the `init` command."""

import json
from subprocess import check_call


def test_init_w_output(gcfpack_invoke_cmdline_w_options: tuple[str]):
    """Test a JSON file is created."""

    output_file = gcfpack_invoke_cmdline_w_options[-1]

    check_call(gcfpack_invoke_cmdline_w_options)

    with open(output_file, "r") as f:
        json.load(f)
