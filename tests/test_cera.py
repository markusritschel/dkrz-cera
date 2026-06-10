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

import pandas as pd
import pytest

from dkrz_cera import Cera, CeraQuery


@pytest.fixture
def cera():
    return Cera()


@pytest.fixture
def cera_query(cera):
    return cera.search(
        variable_s="tas", model_s="ACCESS1-0", qc_experiment_s="historical"
    )


def test_cera(cera):
    assert type(cera.login_url) is str


def test_cera_query(cera_query):
    assert type(cera_query) is CeraQuery
    assert type(cera_query.df) is pd.DataFrame
    assert type(cera_query.parent) is Cera
    assert len(cera_query.df) == 13


def test_cera_to_jblob(cera_query, tmpdir):
    jblob_file = tmpdir.join("jblob_pytest_file.sh")
    cera_query.to_jblob(tmpdir.join("/donwloads/"), jblob_file)
    assert os.path.exists(jblob_file)
    os.remove(jblob_file)


# --- Credential source unit tests ---


def _get_creds(cera_instance):
    """Access name-mangled private attributes for test assertions."""
    return cera_instance._Cera__username, cera_instance._Cera__password


def _clear_cera_env(monkeypatch):
    monkeypatch.delenv("CERA_USER", raising=False)
    monkeypatch.delenv("CERA_PASSWORD", raising=False)
    monkeypatch.delenv("CERA_PASS", raising=False)


def test_credentials_from_env_vars_password(monkeypatch):
    """CERA_USER + CERA_PASSWORD env vars are the highest-priority source."""
    monkeypatch.setenv("CERA_USER", "envuser")
    monkeypatch.setenv("CERA_PASSWORD", "envpass")
    monkeypatch.delenv("CERA_PASS", raising=False)

    cera = Cera()
    cera.check_access()
    assert _get_creds(cera) == ("envuser", "envpass")


def test_credentials_from_env_vars_pass_alias(monkeypatch):
    """CERA_PASS is accepted as an alias for CERA_PASSWORD."""
    monkeypatch.setenv("CERA_USER", "envuser")
    monkeypatch.delenv("CERA_PASSWORD", raising=False)
    monkeypatch.setenv("CERA_PASS", "aliaspass")

    cera = Cera()
    cera.check_access()
    assert _get_creds(cera) == ("envuser", "aliaspass")


def test_credentials_from_dotenv_cwd(monkeypatch, tmp_path):
    """A .env file in the current working directory is used when env vars are absent."""
    _clear_cera_env(monkeypatch)

    cwd_dir = tmp_path / "cwd"
    cwd_dir.mkdir()
    (cwd_dir / ".env").write_text("CERA_USER=cwduser\nCERA_PASSWORD=cwdpass\n")

    # Point HOME somewhere empty so the home .env cannot interfere.
    fake_home = tmp_path / "home"
    fake_home.mkdir()
    monkeypatch.setenv("HOME", str(fake_home))
    monkeypatch.chdir(cwd_dir)

    cera = Cera()
    cera.check_access()
    assert _get_creds(cera) == ("cwduser", "cwdpass")


def test_credentials_from_dotenv_home(monkeypatch, tmp_path):
    """A .env file in the home directory is used when cwd has no .env."""
    _clear_cera_env(monkeypatch)

    fake_home = tmp_path / "home"
    fake_home.mkdir()
    (fake_home / ".env").write_text("CERA_USER=homeuser\nCERA_PASSWORD=homepass\n")
    monkeypatch.setenv("HOME", str(fake_home))

    # cwd has no .env
    cwd_dir = tmp_path / "cwd"
    cwd_dir.mkdir()
    monkeypatch.chdir(cwd_dir)

    cera = Cera()
    cera.check_access()
    assert _get_creds(cera) == ("homeuser", "homepass")


def test_credentials_from_netrc(monkeypatch, tmp_path):
    """~/.netrc is used as the last fallback when no env vars or .env files are present."""
    _clear_cera_env(monkeypatch)

    fake_home = tmp_path / "home"
    fake_home.mkdir()
    (fake_home / ".netrc").write_text(
        "machine cera-www.dkrz.de login netrcuser password netrcpass\n"
    )
    monkeypatch.setenv("HOME", str(fake_home))

    cwd_dir = tmp_path / "cwd"
    cwd_dir.mkdir()
    monkeypatch.chdir(cwd_dir)

    cera = Cera()
    cera.check_access()
    assert _get_creds(cera) == ("netrcuser", "netrcpass")
