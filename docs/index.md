![](_static/logo.png)

## Introduction

Welcome to the documentation of DKRZ-CERA!

This package provides an interface to the CERA database of the DKRZ (Deutsches Klimarechenzentrum).


## Getting Started

### Installation

#### Install via pip

The easiest way to install the package is via pip directly from this repository:

```bash
$ pip install git+https://github.com/markusritschel/dkrz-cera.git
```

#### Clone repo and install locally

Alternatively, clone the repo and use the *Make* targets provided.
First, run

```bash
make conda-env
# or alternatively
make install-requirements
```

to install the required packages either via `conda` or `pip`, followed by

```bash
make src-available
```

to make the project's routines (located in `src`) available for import.

### Usage

The Makefile contains the central entry points for common tasks related to this project.

For scripts, the package can be imported and used as follows:

```python
import dkrz_cera
```

### Test code

You can run

```bash
make tests
```

to run the tests via `pytest`.


## Contact

For any questions or issues, please contact me via git@markusritschel.de or open an [issue](https://github.com/markusritschel/dkrz-cera/issues).





```{toctree}
:hidden:
:caption: Main navigation

getting-started
commands
```


```{toctree}
:hidden:
:caption: Project information

api/index
bibliography
license
README <readme>
```
