"""CLI command implementations."""

import click

from . import gcf, meta


def initialise_sample_description_file(path: str):
    """Create a new example GCF file description JSON file.

    :param path: Path to the output file.
    """

    data = meta.create_sample_metadata_object()

    with open(path, "w", encoding="utf-8") as outf:
        meta.store_metadata(outf, data)


def validate_description_file(path: str):
    """Dry-run version of `create_gcf_file()`.

    :param path: Description file path.
    """

    with open(path, "r", encoding="utf-8") as description_file:
        meta.load_metadata(description_file)

    click.echo("GCF description is valid.")


def create_gcf_file(description_path: str, gcf_path: str):
    """Create a GCF file from its description.

    :param description_path: Description file path.
    :param gcf_path: Destination file path.
    """
    with open(description_path, "r", encoding="utf-8") as description_file:
        description = meta.load_metadata(description_file)

    header, resources = gcf.create_gcf_file(description)
    gcf.write_gcf_file(gcf_path, header, resources)
