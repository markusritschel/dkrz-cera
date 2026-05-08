#!/usr/bin/env python
# -*- coding utf-8 -*-
#
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  kontakt@markusritschel.de
# Date:   17/06/2020
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
import os
from unittest.mock import patch

import pandas as pd
import pytest
from click.testing import CliRunner

from dkrz_cera import Cera, CeraQuery
from dkrz_cera.cli import main


@pytest.fixture
def cera():
    return Cera()


@pytest.fixture
def cera_query(cera):
    return cera.search(
        variable_s="tas", model_s="ACCESS1-0", qc_experiment_s="historical"
    )


def test_cera(cera):
    assert type(cera.login_url) == str


def test_cera_query(cera_query):
    assert type(cera_query) == CeraQuery
    assert type(cera_query.df) == pd.DataFrame
    assert type(cera_query.parent) == Cera
    assert len(cera_query.df) == 13


def test_cera_to_jblob(cera_query, tmpdir):
    jblob_file = tmpdir.join("jblob_pytest_file.sh")
    # check_access requires real credentials; mock it so the file-creation logic is tested
    with patch.object(cera_query.parent, "check_access"):
        cera_query.to_jblob(str(tmpdir.join("downloads")), jblob_file)
    assert os.path.exists(jblob_file) == True
    os.remove(jblob_file)


# ---------------------------------------------------------------------------
# MYL-13: credential resolution
# ---------------------------------------------------------------------------


def test_credentials_from_env_vars(cera, monkeypatch):
    monkeypatch.setenv("CERA_USER", "testuser")
    monkeypatch.setenv("CERA_PASSWORD", "testpass")
    # _Cera__get_credentials is the name-mangled form of __get_credentials
    cera._Cera__get_credentials()
    assert cera._Cera__username == "testuser"
    assert cera._Cera__password == "testpass"


def test_credentials_from_env_vars_cera_pass_alias(cera, monkeypatch):
    monkeypatch.setenv("CERA_USER", "testuser")
    monkeypatch.delenv("CERA_PASSWORD", raising=False)
    monkeypatch.setenv("CERA_PASS", "aliaspass")
    cera._Cera__get_credentials()
    assert cera._Cera__username == "testuser"
    assert cera._Cera__password == "aliaspass"


def test_credentials_from_dotenv(cera, tmp_path, monkeypatch):
    monkeypatch.delenv("CERA_USER", raising=False)
    monkeypatch.delenv("CERA_PASSWORD", raising=False)
    monkeypatch.delenv("CERA_PASS", raising=False)
    # Write a .env file in a temp dir and make it cwd
    env_file = tmp_path / ".env"
    env_file.write_text("CERA_USER=dotenvuser\nCERA_PASSWORD=dotenvpass\n")
    monkeypatch.chdir(tmp_path)
    cera._Cera__get_credentials()
    assert cera._Cera__username == "dotenvuser"
    assert cera._Cera__password == "dotenvpass"


def test_credentials_from_netrc(cera, tmp_path, monkeypatch):
    monkeypatch.delenv("CERA_USER", raising=False)
    monkeypatch.delenv("CERA_PASSWORD", raising=False)
    monkeypatch.delenv("CERA_PASS", raising=False)
    # No .env in cwd or home
    monkeypatch.chdir(tmp_path)
    netrc = tmp_path / ".netrc"
    netrc.write_text("machine cera-www.dkrz.de login netrcuser password netrcpass\n")
    monkeypatch.setenv("HOME", str(tmp_path))
    cera._Cera__get_credentials()
    assert cera._Cera__username == "netrcuser"
    assert cera._Cera__password == "netrcpass"


def test_credentials_env_vars_take_priority_over_dotenv(cera, tmp_path, monkeypatch):
    monkeypatch.setenv("CERA_USER", "envuser")
    monkeypatch.setenv("CERA_PASSWORD", "envpass")
    env_file = tmp_path / ".env"
    env_file.write_text("CERA_USER=dotenvuser\nCERA_PASSWORD=dotenvpass\n")
    monkeypatch.chdir(tmp_path)
    cera._Cera__get_credentials()
    assert cera._Cera__username == "envuser"


# ---------------------------------------------------------------------------
# MYL-14: check_access validation
# ---------------------------------------------------------------------------


def test_check_access_raises_when_no_credentials(cera, tmp_path, monkeypatch):
    monkeypatch.delenv("CERA_USER", raising=False)
    monkeypatch.delenv("CERA_PASSWORD", raising=False)
    monkeypatch.delenv("CERA_PASS", raising=False)
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    with pytest.raises(PermissionError, match="No CERA credentials found"):
        cera.check_access()


def test_check_access_raises_on_rejected_credentials(cera, monkeypatch):
    monkeypatch.setenv("CERA_USER", "baduser")
    monkeypatch.setenv("CERA_PASSWORD", "badpass")

    import requests

    mock_resp = requests.Response()
    mock_resp.status_code = 302
    mock_resp.headers["Location"] = (
        "https://cera-www.dkrz.de/WDCC/ui/cerasearch/login?error"
    )

    with patch("requests.post", return_value=mock_resp):
        with pytest.raises(PermissionError, match="rejected credentials"):
            cera.check_access()


def test_check_access_warns_on_network_error(cera, monkeypatch, capsys):
    monkeypatch.setenv("CERA_USER", "user")
    monkeypatch.setenv("CERA_PASSWORD", "pass")

    import requests

    with patch("requests.post", side_effect=requests.ConnectionError("unreachable")):
        # Should NOT raise — network errors are warnings only
        cera.check_access()

    captured = capsys.readouterr()
    assert "Warning" in captured.out


# ---------------------------------------------------------------------------
# MYL-15: CLI smoke tests
# ---------------------------------------------------------------------------


def test_cli_help():
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "search" in result.output
    assert "download" in result.output
    assert "unzip" in result.output


def test_cli_search_help():
    runner = CliRunner()
    result = runner.invoke(main, ["search", "--help"])
    assert result.exit_code == 0
    assert "--variable" in result.output


def test_cli_download_help():
    runner = CliRunner()
    result = runner.invoke(main, ["download", "--help"])
    assert result.exit_code == 0
    assert "--variable" in result.output
    assert "--path" in result.output


def test_cli_unzip_help():
    runner = CliRunner()
    result = runner.invoke(main, ["unzip", "--help"])
    assert result.exit_code == 0
    assert "--path" in result.output


def test_cli_search_invokes_cera(monkeypatch):
    from dkrz_cera import CeraQuery

    mock_df = pd.DataFrame(
        [
            [
                "a",
                "ACCESS1-0",
                "historical",
                "tas",
                "mon",
                "CMIP5 historical ACCESS1-0 mon atmos Amon tas r1i1p1",
                "CMIP5",
                "NetCDF",
            ]
        ],
        columns=[
            "entry_acronym_s",
            "model_s",
            "qc_experiment_s",
            "variable_s",
            "frequency_s",
            "entry_name_s",
            "project_acronym_ss",
            "format_acronym_s",
        ],
    )
    mock_query = CeraQuery.__new__(CeraQuery)
    mock_query._CeraQuery__results_dict = {}

    with patch.object(Cera, "search", return_value=mock_query):
        with patch.object(
            CeraQuery, "df", new_callable=lambda: property(lambda self: mock_df)
        ):
            runner = CliRunner()
            result = runner.invoke(main, ["search", "--variable", "tas"])
            assert result.exit_code == 0
