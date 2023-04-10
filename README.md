# science-knowledge-distiller

## Build instructions

### Ubuntu

### Mac OS X

### Windows

Prerequisites

**1. Install Python 3.10: https://www.python.org/downloads/release/python-3100/**

Note: run installer as administrator and select checkbox "Add Python 3.10 to PATH"

After installation, verify that python's executable is callable from cmd:
```console
> python --version
Python 3.10.0

```

**2. Install R 4.2.3: https://cran.r-project.org/bin/windows/base/**

**3. Install R Tools 4.2: https://cran.r-project.org/bin/windows/Rtools/rtools42/rtools.html**

**4. Add `Rscript` executable file to PATH environment variable**

`Rscript.exe` is located somewhere like: `C:\Program Files\R\R-4.2.3\bin`

Copy your path to the directory where `Rscript.exe` is located and add that path to the PATH (https://www.architectryan.com/2018/03/17/add-to-the-path-on-windows-10/)

Then open new cmd and verify that `Rscript` is callable from cmd:
```console
> Rscript --version
Rscript (R) version 4.2.3 (2023-03-15)

```

Now let's set up environment for our project (`git` is required for installation)

Open new cmd **as administrator** and do the following steps:

**1. Clone project**
through https
```console
> git clone https://github.com/alcatraz-rm/scientific-knowledge-distiller.git
```
or through ssh
```console
> git clone git@github.com:alcatraz-rm/scientific-knowledge-distiller.git
```

**2. Go to the project's directory and checkout to the `dev` branch**
```console
> cd scientific-knowledge-distiller
> git checkout dev
```

**3. Create Python 3.10 virtual environment**
```console
scientific-knowledge-distiller> python -m venv venv
```

And activate it
```console
scientific-knowledge-distiller> venv\Scripts\activate
```

**4. Install python dependencies**
```console
(venv) scientific-knowledge-distiller> pip install -r requirements_darwin.txt
```

**5. Go to `deduplication` directory and install R dependencies:**
```console
(venv) scientific-knowledge-distiller> cd deduplication
(venv) scientific-knowledge-distiller\deduplication> Rscript install.r
```

**6. Create and fill `.env` file with the following lines**
```console
CORE_API_KEY=<YOUR-CORE-API-KEY>
UNPAYWALL_EMAIL=<YOUR-EMAIL-FOR-UNPAYWALL>
SEMANTIC_SCHOLAR_API_KEY=<YOUR-SEMANTIC_SCHOLAR-KEY>
TOKENIZERS_PARALLELISM=true
PAPERS_WITH_CODE_API_KEY=<YOUR-PAPERS_WITH_CODE-API-KEY>
```

That's it!

## Modules

1. Search module is located in [search_engine](./search_engine) directory
2. Deduplication module is located in [deduplication](./deduplication) directory
3. Distiller is located in [distiller](./distiller) directory
4. [ml_sandbox](./ml_sandbox) is used for testing and contains bunch of jupyter notebooks with some drafts

Each module (except ml_sandbox) contains readme inside.
