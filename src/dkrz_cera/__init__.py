# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  git@markusritschel.de
# Date:   2024-06-23
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
"""Provide global path variables, version information, and utility functions for the package."""
from pathlib import Path

from dotenv import find_dotenv, load_dotenv

from .cera_access import *
from .file_processing import *

__version__ = "0.1.0"


# Make some of the basic directories globally available in your environment
BASE_DIR = Path(__file__).resolve().parents[2]
LOG_DIR = BASE_DIR / "logs"
jupyter_startup_script = BASE_DIR / "notebooks/jupyter_startup.ipy"

# find .env automagically by walking up directories until it's found
dotenv_path = find_dotenv()
# load up the entries as environment variables
load_dotenv(dotenv_path)
