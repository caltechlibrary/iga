# Installation

IGA can be installed as either (or both) a command-line program on your computer or a [GitHub Action](https://docs.github.com/en/actions) in a GitHub repository.

## IGA as a normal program

Please choose an approach that suits your situation and preferences. Then, after installation, proceed to (1) [get an InvenioRDM token](quick-start.md#getting-an-inveniordm-token) and (2) [configure IGA for command-line use](quick-start.md#configuring-a-local-iga).


### Installation alternative 1: installing IGA using `pipx`

[Pipx](https://pypa.github.io/pipx/) lets you install Python programs in a way that isolates Python dependencies from other Python programs on your system, and yet the resulting `iga` command can be run from any shell and directory &ndash; like any normal program on your computer. If you use `pipx` on your system, you can install IGA with the following command:
```sh
pipx install iga
```


### Installation alternative 2: installing IGA using `pip`

IGA is available from the [Python package repository PyPI](https://pypi.org) and can be installed using [`pip`](https://pip.pypa.io/en/stable/installing/):
```sh
python3 -m pip install iga
```

As an alternative to getting it from [PyPI](https://pypi.org), you can install `iga` directly from GitHub:
```sh
python3 -m pip install git+https://github.com/caltechlibrary/iga.git
```

_If you already installed IGA once before_, and want to update to the latest version, add `--upgrade` to the end of either command line above.


### Installation alternative 3: installing IGA from sources

If  you prefer to install IGA directly from the source code, first obtain a copy by either downloading the source archive from the [IGA releases page on GitHub](https://github.com/caltechlibrary/iga/releases), or by using `git` to clone the repository to a location on your computer. For example,
```sh
git clone https://github.com/caltechlibrary/iga
```

Next, after getting a copy of the files,  run `setup.py` inside the code directory:
```sh
cd iga
python3 setup.py install
```


(iga_as_a_github_action)=
## IGA as a GitHub workflow

A [GitHub Actions](https://docs.github.com/en/actions) workflow is an automated process that runs on GitHub's servers under control of a file in your repository. Follow these steps to create the IGA workflow file:

1. In the main branch of your GitHub repository, create a `.github/workflows` directory
2. In the `.github/workflows` directory, create a file named (e.g.) `iga.yml` and copy the following content (which is also available as file [`sample-workflow.yml`](https://github.com/caltechlibrary/iga/blob/main/sample-workflow.yml) in the GitHub repository for IGA):
    ```{literalinclude} ../sample-workflow.yml
    :language: yaml
    ```
3. **Edit the value of the `INVENIO_SERVER` variable near the top of the file above** ↑. For CaltechDATA the value should be `https://data.caltech.edu`.
4. Optionally, change the [values of other options (`parent_record`, `community`, etc.)](https://caltechlibrary.github.io/iga/gha-usage.html#input-parameters)
5. Save the file, commit the changes to git, and push your changes to GitHub

Once you have installed the GitHub Action workflow for IGA, the next steps are (1) [get an InvenioRDM token](quick-start.md#getting-an-inveniordm-token) and (2) [configure the GitHub Action workflow](quick-start.md#configuring-a-github-action).
