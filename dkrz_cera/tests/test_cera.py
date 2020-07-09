#!/usr/bin/env python
# -*- coding utf-8 -*-
#
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  kontakt@markusritschel.de
# Date:   17/06/2020
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
import pytest
from dkrz_cera import Cera, CeraQuery
import pandas as pd
import os


@pytest.fixture
def cera():
    return Cera()


@pytest.fixture
def cera_query(cera):
    return cera.search(variable_s='tas', model_s='ACCESS1-0', qc_experiment_s='historical')


def test_cera(cera):
    assert type(cera.login_url) == str


def test_cera_query(cera_query):
    assert type(cera_query) == CeraQuery
    assert type(cera_query.df) == pd.DataFrame
    assert type(cera_query.parent) == Cera
    assert len(cera_query.df) == 13


def test_cera_to_jblob(cera_query, tmpdir):
    jblob_file = tmpdir.join('jblob_pytest_file.sh')
    cera_query.to_jblob(tmpdir.join('/donwloads/'), jblob_file)
    assert os.path.exists(jblob_file) == True
    os.remove(jblob_file)
