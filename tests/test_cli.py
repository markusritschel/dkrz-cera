#!/usr/bin/env python
# -*- coding utf-8 -*-
"""Smoke tests for the dkrz-cera CLI."""

import pytest
from click.testing import CliRunner

from dkrz_cera.cli import main


@pytest.fixture
def runner():
    return CliRunner()


def test_main_help(runner):
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "search" in result.output
    assert "download" in result.output
    assert "unzip" in result.output


def test_search_help(runner):
    result = runner.invoke(main, ["search", "--help"])
    assert result.exit_code == 0
    assert "--variable" in result.output
    assert "--model" in result.output
    assert "--experiment" in result.output
    assert "--frequency" in result.output
    assert "--project" in result.output
    assert "--format" in result.output


def test_download_help(runner):
    result = runner.invoke(main, ["download", "--help"])
    assert result.exit_code == 0
    assert "--variable" in result.output
    assert "--model" in result.output
    assert "--experiment" in result.output
    assert "--path" in result.output
    assert "--jblob-file" in result.output


def test_unzip_help(runner):
    result = runner.invoke(main, ["unzip", "--help"])
    assert result.exit_code == 0
    assert "--path" in result.output
