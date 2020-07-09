#!/usr/bin/env python
# -*- coding utf-8 -*-
#
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
# Author: Markus Ritschel
# eMail:  kontakt@markusritschel.de
# Date:   18/06/2020
# %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
#
import os
from pathlib import Path
from zipfile import ZipFile


def unzip_files(path):
    """
    Unzip recursively all files in a specific directory tree.

    Parameters
    ----------
    path : str
        The directory which contains the zip files to be extracted.
    """
    path = Path(path).expanduser()

    count_zips = 0
    count_netcdfs = 0
    while True:
        # all_zip_files = glob.glob('*.zip')
        all_zip_files = [x for x in path.rglob('*.zip') if x.is_file()]
        count_zips += len(all_zip_files)
        if not all_zip_files:
            print("No zip files found.")
            break
        for zip_file in all_zip_files:
            # TODO: maybe parallel processing?
            netcdfs_in_zip = len([f for f in ZipFile(zip_file).namelist() if f.endswith('.nc')])
            count_netcdfs += netcdfs_in_zip
            print("Unpacking {} netCDF files from {}...".format(netcdfs_in_zip, zip_file))
            ZipFile(zip_file).extractall(path=os.path.dirname(zip_file))
            os.remove(zip_file)
    print(f'{count_netcdfs} netCDF files out of {count_zips} zip files successfully extracted. '
          f'Deleted zip files after extraction.')

    return


if __name__ == '__main__':
    DOWNLOAD_DIR = os.path.join(os.getenv('HOME'), "work/cmip5-download")
    unzip_files(DOWNLOAD_DIR)
