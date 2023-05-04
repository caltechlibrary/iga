# Installation

## IGA as a normal program

IGA can be used as an ordinary command-line program in macOS, Windows, and Linux.There are multiple ways of installing IGA on your computer.  Please choose the alternative that suits you.

### Alternative 1: installing IGA using `pipx`

[Pipx](https://pypa.github.io/pipx/) lets you install Python programs in a way that isolates Python dependencies, and yet the resulting `iga` command can be run from any shell and directory &ndash; like any normal program on your computer. If you use `pipx` on your system, you can install IGA with the following command:
```sh
pipx install iga
```

Pipx can also let you run IGA directly using `pipx run iga`, although in that case, you must always prefix every IGA command with `pipx run`.  Consult the [documentation for `pipx run`](https://github.com/pypa/pipx#walkthrough-running-an-application-in-a-temporary-virtual-environment) for more information.


### Alternative 2: installing IGA using `pip`

You should be able to install `iga` with [`pip`](https://pip.pypa.io/en/stable/installing/) for Python&nbsp;3.  To install `iga` from the [Python package repository (PyPI)](https://pypi.org), run the following command:
```sh
python3 -m pip install iga
```

As an alternative to getting it from [PyPI](https://pypi.org), you can use `pip` to install `iga` directly from GitHub:
```sh
python3 -m pip install git+https://github.com/caltechlibrary/iga.git
```

_If you already installed IGA once before_, and want to update to the latest version, add `--upgrade` to the end of either command line above.


### Alternative 3: installing IGA from sources

If  you prefer to install IGA directly from the source code, you can do that too. To get a copy of the files, you can clone the GitHub repository:
```sh
git clone https://github.com/caltechlibrary/iga
```

Alternatively, you can download the software source files as a ZIP archive directly from your browser using this link: <https://github.com/caltechlibrary/iga/archive/refs/heads/main.zip>

Next, after getting a copy of the files,  run `setup.py` inside the code directory:
```sh
cd iga
python3 setup.py install
```


## IGA as a GitHub Action
