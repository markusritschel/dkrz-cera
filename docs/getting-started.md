# Getting started

## Installation

Clone the repository to your machine
```bash
git clone https://github.com/markusritschel/dkrz-cera.git
```
and then install the package by running
```
python setup.py install
```
in the directory of the cloned repository.


## Usage

The database can be scraped by creating an instance of the Cera class and using it's `search` method:
```python
from dkrz_cera import Cera
cera = Cera()
cera.search(variable_s='tas', model_s='ACCESS1-0', qc_experiment_s='historical')
```
This yields a `CeraQuery` object, which itself provides a tabular view of the request results by the `.df` attribute,
as well as a method `to_jblob()`, which creates a bash file executable by Jblob for eventually downloading the datasets from CERA.
When running this bash file, a directory structure gets created according to the CMIP standards, i.e.
```
<activity>/
    <product>/
        <institute>/
            <model>/
                <experiment>/
                    <frequency>/
                        <modeling realm>/
                            <MIP table>/
                                <ensemble member>/
                                    <version number>/
                                        <variable name>/
```
This structure is created by hands of the `entry_name_s` provided in each dataset.
(However, in some exceptions it can happen that this entry_name_s value is not complying the CMIP standards.)

The data sets get automatically downloaded into the respective directory.
While some of them are already downloaded as netCDF files, others exist primarily as zip files and still need to be extracted.
This can be done by using the function `unzip_files()` which takes the root path (parent of the `<activity>` directory)
as a mandatory argument.
