#!/usr/bin/env python
# -*- coding utf-8 -*-
#
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  kontakt@markusritschel.de
# Date:   17/06/2020
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
from pkg_resources import get_distribution, DistributionNotFound
from .cera_access import *

try:
    # Change here if project is renamed and does not equal the package name
    dist_name = 'dkrz-cera'
    __version__ = get_distribution(dist_name).version
except DistributionNotFound:
    __version__ = 'unknown'
finally:
    del get_distribution, DistributionNotFound
