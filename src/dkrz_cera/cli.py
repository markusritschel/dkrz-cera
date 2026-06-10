# -*- coding utf-8 -*-
#
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2024-06-23
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
"""CLI script for dkrz_cera."""

import sys

import click
from rich.console import Console
from rich.table import Table
import typer

app = typer.Typer()
console = Console()


@click.group()
def main():
    """CLI script for dkrz_cera."""
    ...


@main.command()
@click.option("--variable", required=True, help="Variable name (e.g. tas, pr)")
@click.option("--model", required=True, help="Model name (e.g. ACCESS1-0)")
@click.option("--experiment", required=True, help="Experiment name (e.g. historical)")
@click.option("--frequency", default=None, help="Temporal frequency (e.g. mon, day)")
@click.option("--project", default=None, help="Project acronym (e.g. CMIP5)")
@click.option("--format", "fmt", default=None, help="Format acronym (e.g. NetCDF)")
def search(variable, model, experiment, frequency, project, fmt):
    """Search the CERA database and print a summary table of matching datasets."""
    from dkrz_cera import Cera

    query = dict(variable_s=variable, model_s=model, qc_experiment_s=experiment)
    if frequency:
        query["frequency_s"] = frequency
    if project:
        query["project_acronym_s"] = project
    if fmt:
        query["format_acronym_s"] = fmt

    try:
        cera = Cera()
        result = cera.search(**query)
    except Exception as exc:
        raise click.ClickException(f"Search failed: {exc}")

    if result is None:
        raise click.ClickException("No datasets found matching the given criteria.")

    df = result.df
    table = Table(show_header=True, header_style="bold cyan")
    for col in df.columns:
        table.add_column(col)
    for row in df.itertuples(index=False):
        table.add_row(*[str(v) for v in row])
    console.print(table)


@main.command()
@click.option("--variable", required=True, help="Variable name (e.g. tas, pr)")
@click.option("--model", required=True, help="Model name (e.g. ACCESS1-0)")
@click.option("--experiment", required=True, help="Experiment name (e.g. historical)")
@click.option("--path", required=True, help="Download directory for retrieved datasets")
@click.option("--frequency", default=None, help="Temporal frequency (e.g. mon, day)")
@click.option("--project", default=None, help="Project acronym (e.g. CMIP5)")
@click.option("--format", "fmt", default=None, help="Format acronym (e.g. NetCDF)")
@click.option(
    "--jblob-file",
    default=None,
    help="Output path for the generated jblob shell script",
)
def download(variable, model, experiment, path, frequency, project, fmt, jblob_file):
    """Search CERA and write a jblob download script to disk."""
    from dkrz_cera import Cera

    query = dict(variable_s=variable, model_s=model, qc_experiment_s=experiment)
    if frequency:
        query["frequency_s"] = frequency
    if project:
        query["project_acronym_s"] = project
    if fmt:
        query["format_acronym_s"] = fmt

    try:
        cera = Cera()
        result = cera.search(**query)
    except Exception as exc:
        raise click.ClickException(f"Search failed: {exc}")

    if result is None:
        raise click.ClickException("No datasets found matching the given criteria.")

    try:
        result.to_jblob(path, file=jblob_file)
    except Exception as exc:
        raise click.ClickException(f"Failed to create jblob script: {exc}")


@main.command()
@click.option("--path", required=True, help="Directory containing zip files to extract")
def unzip(path):
    """Recursively extract zip files in a directory."""
    from dkrz_cera import unzip_files

    try:
        unzip_files(path)
    except Exception as exc:
        raise click.ClickException(f"Unzip failed: {exc}")


if __name__ == "__main__":
    sys.exit(main())
