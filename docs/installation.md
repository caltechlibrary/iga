# Installation

IGA can be installed as either (or both) a command-line program on your computer or a [GitHub Action](https://docs.github.com/en/actions) in a GitHub repository.

## IGA as a normal program

Please choose an approach that suits your situation and preferences.

### Alternative 1: installing IGA using `pipx`

[Pipx](https://pypa.github.io/pipx/) lets you install Python programs in a way that isolates Python dependencies, and yet the resulting `iga` command can be run from any shell and directory &ndash; like any normal program on your computer. If you use `pipx` on your system, you can install IGA with the following command:
```sh
pipx install iga
```

Pipx can also let you run IGA directly using `pipx run iga`, although in that case, you must always prefix every IGA command with `pipx run`.  Consult the [documentation for `pipx run`](https://github.com/pypa/pipx#walkthrough-running-an-application-in-a-temporary-virtual-environment) for more information.


### Alternative 2: installing IGA using `pip`

IGA is available from the [Python package repository PyPI](https://pypi.org) and can be installed using [`pip`](https://pip.pypa.io/en/stable/installing/):
```sh
python3 -m pip install iga
```

As an alternative to getting it from [PyPI](https://pypi.org), you can install `iga` directly from GitHub:
```sh
python3 -m pip install git+https://github.com/caltechlibrary/iga.git
```

_If you already installed IGA once before_, and want to update to the latest version, add `--upgrade` to the end of either command line above.


### Alternative 3: installing IGA from sources

If  you prefer to install IGA directly from the source code, first obtain a copy by either downloading the source archive from the [IGA releases page on GitHub](https://github.com/caltechlibrary/iga/releases), or by using `git` to clone the repository to a location on your computer. For example,
```sh
git clone https://github.com/caltechlibrary/iga
```

Next, after getting a copy of the files,  run `setup.py` inside the code directory:
```sh
cd iga
python3 setup.py install
```


## IGA as a GitHub workflow

A [GitHub Actions](https://docs.github.com/en/actions) workflow is an automated process that runs on GitHub's servers under control of a file in your repository. Follow these steps to create the IGA workflow file:

1. In the main branch of your GitHub repository, create a `.github/workflows` directory
2. In the `.github/workflows` directory, create a file named (e.g.) `iga.yml` and copy the [following contents](https://raw.githubusercontent.com/caltechlibrary/iga/develop/sample-workflow.yml):
    ```{literalinclude} ../sample-workflow.yml
    :language: yaml
    ```
3. **Edit the value of the `INVENIO_SERVER` variable near the top of the file above** ↑
4. Optionally, change the [values of other options (`parent_record`, `community`, etc.)](https://caltechlibrary.github.io/iga/gha-usage.html#input-parameters)
5. Save the file, commit the changes to git, and push your changes to GitHub

The sample `.yml` workflow file above is also available from the GitHub repository for IGA as file [`sample-workflow.yml`](https://github.com/caltechlibrary/iga/blob/main/sample-workflow.yml).
