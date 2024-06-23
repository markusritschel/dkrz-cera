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

from __future__ import absolute_import, division, print_function, with_statement
import sys
import click


@click.command()
def main(args=None):
    """Console script for dkrz-cera."""
    click.echo("Replace this message by putting your code into "
               "dkrz-cera.cli.main")
    click.echo("See click documentation at https://click.palletsprojects.com/")
    return None


if __name__ == "__main__":
    sys.exit(main())
