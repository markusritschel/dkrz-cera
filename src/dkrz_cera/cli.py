#!/usr/bin/env python
# -*- coding utf-8 -*-
#
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2024-06-23
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
"""Console script for dkrz-cera."""


import sys

import click

from dkrz_cera.cera_access import Cera
from dkrz_cera.file_processing import unzip_files


@click.group()
def main():
    """Interface to the DKRZ CERA climate data database."""


@main.command()
@click.option("--variable", "-v", required=True, help="Variable name (e.g. tas)")
@click.option("--model", "-m", help="Model name (e.g. ACCESS1-0)")
@click.option("--experiment", "-e", help="Experiment name (e.g. historical)")
@click.option("--frequency", "-f", help="Frequency (e.g. mon, day)")
@click.option("--project", "-p", help="Project acronym (e.g. CMIP5)")
@click.option("--format", "fmt", help="Format acronym (e.g. NetCDF)")
def search(variable, model, experiment, frequency, project, fmt):
    """Search the CERA database and print a summary table of matching datasets."""
    query = {"variable_s": variable}
    if model:
        query["model_s"] = model
    if experiment:
        query["qc_experiment_s"] = experiment
    if frequency:
        query["frequency_s"] = frequency
    if project:
        query["project_acronym_s"] = project
    if fmt:
        query["format_acronym_s"] = fmt

    cera = Cera()
    result = cera.search(**query)
    if result is None:
        click.echo("No datasets found.", err=True)
        sys.exit(1)

    try:
        from rich.console import Console
        from rich.table import Table

        table = Table(title=f"CERA search results ({len(result.df)} datasets)")
        for col in result.df.columns:
            table.add_column(col, overflow="fold")
        for _, row in result.df.iterrows():
            table.add_row(*[str(v) for v in row])
        Console().print(table)
    except ImportError:
        click.echo(result.df.to_string())


@main.command()
@click.option("--variable", "-v", required=True, help="Variable name (e.g. tas)")
@click.option("--model", "-m", help="Model name (e.g. ACCESS1-0)")
@click.option("--experiment", "-e", help="Experiment name (e.g. historical)")
@click.option("--frequency", "-f", help="Frequency (e.g. mon, day)")
@click.option("--project", "-p", help="Project acronym")
@click.option("--format", "fmt", help="Format acronym")
@click.option(
    "--path",
    required=True,
    type=click.Path(),
    help="Directory where datasets will be downloaded.",
)
@click.option(
    "--jblob-file",
    default=None,
    help="Output path for the jblob shell script (default: ~/jblob_cera_download.sh).",
)
def download(variable, model, experiment, frequency, project, fmt, path, jblob_file):
    """Search CERA and write a jblob download script to disk."""
    query = {"variable_s": variable}
    if model:
        query["model_s"] = model
    if experiment:
        query["qc_experiment_s"] = experiment
    if frequency:
        query["frequency_s"] = frequency
    if project:
        query["project_acronym_s"] = project
    if fmt:
        query["format_acronym_s"] = fmt

    cera = Cera()
    result = cera.search(**query)
    if result is None:
        click.echo("No datasets found — nothing to download.", err=True)
        sys.exit(1)

    try:
        result.to_jblob(download_path=path, file=jblob_file)
    except PermissionError as exc:
        click.echo(f"Credential error: {exc}", err=True)
        sys.exit(1)


@main.command()
@click.option(
    "--path",
    required=True,
    type=click.Path(exists=True),
    help="Root directory to recursively unzip.",
)
def unzip(path):
    """Recursively extract all zip files found under PATH."""
    unzip_files(path)


if __name__ == "__main__":
    sys.exit(main())
