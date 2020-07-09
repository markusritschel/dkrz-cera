dkrz-cera
=========
[![GitHub license](https://img.shields.io/github/license/markusritschel/dkrz-cera)](https://github.com/markusritschel/dkrz-cera/blob/master/LICENSE)
![build](https://github.com/markusritschel/dkrz-cera/workflows/build/badge.svg)

This package provides an interface to the CERA database of the DKRZ (_Deutsches Klimarechenzentrum_).
This allows the user to scrape the database for CMIP data, for example, and prepare files for the remote download via 
[Jblob](https://cera-www.dkrz.de/WDCC/ui/cerasearch/info?site=jblob),
a program written in Java and provided by the DKRZ.



Installation
------------
Clone the repository to your machine
```bash
git clone https://github.com/markusritschel/dkrz-cera.git
```
and then install the package by running 
```
python setup.py install
``` 
in the directory of the cloned repository.


Usage
-----
The database can be scraped by creating an instance of the Cera class and using it's `search` method:
```python
from dkrz_cera import Cera
cera = Cera()
cera.search(variable_s='tas', model_s='ACCESS1-0', qc_experiment_s='historical')
```
This yields a CeraQuery object, which itself provides a tabular view of the request results by the `.df` attribute, 
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


ToDos
-----
- [x] Routine for scraping the CERA database based on multiple keywords
- [x] sort files depending on configuration file => creates directory structure automatically during jblob download
- [x] create intake-esm catalog files => this will be implemented in another package
- [ ] Try to validate CERA credentials if present
- [ ] Retrieve CERA credentials either from `.env` file or from environment variable via `os.getenv('CERA_USER')`
- [ ] implement [click](https://click.palletsprojects.com/) for command line tooling


Contact
-------
Feel free to contact me via git@markusritschel.de.
For problems or feature requests please open an [issue](https://github.com/markusritschel/dkrz-cera/issues).
Of course, you are also welcome to contribute and start a pull-request :-)

--------
<p><small>Project based on the <a target="_blank" href="https://drivendata.github.io/cookiecutter-data-science/">cookiecutter data science project template</a>. #cookiecutterdatascience</small></p>
