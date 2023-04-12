"""Main application entry point."""

import click

from . import commands


@click.group()
def cli():
    """Main CLI group."""


@cli.command(help="Create a new GCF file from description.")
@click.option("-n", "--dry-run", help="Validate the description file without creating a GCF file.", default=False)
@click.option("-i", "--description", help="JSON description file.", type=str)
@click.option("-o", "--output", help="Output GCF file.", type=str)
def create(dry_run: bool, description: str, output: str):
    """Create a new GCF file from description."""

    if dry_run:
        commands.validate_description_file(description)
    else:
        commands.create_gcf_file(description, output)


@cli.command(help="Create a new example GCF file description JSON file.")
@click.option("-o", "--output", default="meta.json", help="Output file name.")
def init(output: str):
    """Create a new example GCF file description JSON file."""

    commands.initialise_sample_description_file(output)


if __name__ == "__main__":
    cli()
