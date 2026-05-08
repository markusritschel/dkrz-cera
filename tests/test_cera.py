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
    assert type(cera.login_url) == str


def test_cera_query(cera_query):
    assert type(cera_query) == CeraQuery
    assert type(cera_query.df) == pd.DataFrame
    assert type(cera_query.parent) == Cera
    assert len(cera_query.df) == 13


def test_cera_to_jblob(cera_query, tmpdir):
    jblob_file = tmpdir.join("jblob_pytest_file.sh")
    cera_query.to_jblob(tmpdir.join("/donwloads/"), jblob_file)
    assert os.path.exists(jblob_file) == True
    os.remove(jblob_file)


# --- check_access tests ---


def test_check_access_raises_when_no_credentials(cera):
    """check_access() must raise PermissionError when credentials are absent."""
    from unittest.mock import patch

    # Patch __get_credentials so it never populates username/password
    with patch.object(cera, "_Cera__get_credentials"):
        with pytest.raises(PermissionError, match="No CERA credentials found"):
            cera.check_access()


def test_check_access_warns_on_network_error(cera):
    """check_access() must emit a UserWarning when the server is unreachable."""
    from unittest.mock import patch

    import requests

    # Inject credentials directly via name-mangled attributes
    cera._Cera__username = "testuser"
    cera._Cera__password = "testpass"

    with patch.object(cera, "_Cera__get_credentials"):
        with patch("dkrz_cera.cera_access.requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.ConnectionError("unreachable")
            with pytest.warns(UserWarning, match="Could not reach CERA server"):
                result = cera.check_access()
    assert result is True


def test_check_access_warns_on_timeout(cera):
    """check_access() must emit a UserWarning when the server times out."""
    from unittest.mock import patch

    import requests

    cera._Cera__username = "testuser"
    cera._Cera__password = "testpass"

    with patch.object(cera, "_Cera__get_credentials"):
        with patch("dkrz_cera.cera_access.requests.post") as mock_post:
            mock_post.side_effect = requests.exceptions.Timeout()
            with pytest.warns(UserWarning, match="timed out"):
                result = cera.check_access()
    assert result is True


def test_check_access_raises_on_server_rejection(cera):
    """check_access() must raise PermissionError when server redirects back to login."""
    from unittest.mock import MagicMock, patch

    cera._Cera__username = "baduser"
    cera._Cera__password = "badpass"

    mock_response = MagicMock()
    mock_response.url = "https://cera-www.dkrz.de/WDCC/ui/cerasearch/login"
    mock_response.raise_for_status.return_value = None

    with patch.object(cera, "_Cera__get_credentials"):
        with patch("dkrz_cera.cera_access.requests.post", return_value=mock_response):
            with pytest.raises(PermissionError, match="rejected credentials"):
                cera.check_access()
