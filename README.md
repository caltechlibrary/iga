# IGA<img width="12%" align="right" src="https://github.com/caltechlibrary/iga/raw/main/docs/_static/media/cloud-upload.png">

IGA is the _InvenioRDM GitHub Archiver_, a standalone program as well as a GitHub Action that lets you automatically archive GitHub software releases in an [InvenioRDM](https://inveniosoftware.org/products/rdm/) repository.

[![License](https://img.shields.io/badge/License-BSD--like-lightgrey.svg?style=flat-square)](https://github.com/caltechlibrary/iga/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-brightgreen.svg?style=flat-square)](https://www.python.org/downloads/release/python-390/)
[![Latest release](https://img.shields.io/github/v/release/caltechlibrary/iga.svg?color=b44e88&style=flat-square)](https://github.com/caltechlibrary/iga/releases)


## Table of contents

* [Introduction](#introduction)
* [Installation](#installation)
* [Usage](#usage)
* [Known issues and limitations](#known-issues-and-limitations)
* [Getting help](#getting-help)
* [Contributing](#contributing)
* [License](#license)
* [Acknowledgments](#authors-and-acknowledgments)


## Introduction

[InvenioRDM](https://inveniosoftware.org/products/rdm/) is a research data management (RDM) repository platform based on the [Invenio Framework](https://inveniosoftware.org/products/framework/) and [Zenodo](https://www.zenodo.org). At institutions like Caltech, InvenioRDM is used as the basis for institutional repositories such as [CaltechDATA](https://data.caltech.edu). Of particular interest to software developers is that a repository like [CaltechDATA](https://data.caltech.edu) offers the means to preserve software projects in a long-term archive managed by their institution.

The _InvenioRDM GitHub Archiver_ (IGA) is a tool for sending software releases from GitHub to an InvenioRDM-based repository server. IGA can be invoked from the command line; it also can be set up as a [GitHub Action](https://docs.github.com/en/actions) to automate the archiving of GitHub software releases in an InvenioRDM repository. Here are some of IGA's other notable features:
* Automatic extraction of metadata from the GitHub release, the GitHub repository, and [`codemeta.json`](https://codemeta.github.io) and/or [`CITATION.cff`](https://citation-file-format.github.io) files if they exist in the repository
* Thorough coverage of [InvenioRDM record metadata](https://inveniordm.docs.cern.ch/reference/metadata) using painstaking procedures
* Automatic recognition of common identifier types that often appear CodeMeta and CFF files, such as [ORCID](https://orcid.org), [ROR](https://ror.org), [DOI](https://www.doi.org), [arXiV](https://arxiv.org), [PMCID/PMID](https://www.ncbi.nlm.nih.gov/pmc/about/public-access-info/), and others
* Automatic lookup of human names in [ORCID.org](https://orcid.org) if needed (assuming ORCID id's are provided)
* Automatic lookup of organization names in [ROR](https://ror.org) (assuming ROR id's are provided)
* Automatic lookup of publication data in [DOI.org](https://www.doi.org), [PubMed]((https://www.ncbi.nlm.nih.gov/pmc/about/public-access-info/)), Google Books, & other sources if needed
* Automatic splitting of human names into family and given names using [ML](https://en.wikipedia.org/wiki/Machine_learning)-based methods, if necessary, to comply with InvenioRDM requirements
* Support for overriding the metadata record it creates, for complete control if you need it
* Support for InvenioRDM [communities](https://invenio-communities.readthedocs.io/en/latest/)
* Ability to use the GitHub API without a [GitHub access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) in many cases
* Extensive use of logging so you can see what's going on under the hood


## Installation

(Note: at this time, only the command-line version of IGA is available.) There are multiple ways of installing IGA.  Please choose the alternative that suits you.

### _Alternative 1: installing IGA using `pipx`_

[Pipx](https://pypa.github.io/pipx/) lets you install Python programs in a way that isolates Python dependencies, and yet the resulting `iga` command can be run from any shell and directory &ndash; like any normal program on your computer. If you use `pipx` on your system, you can install IGA with the following command:
```sh
pipx install iga
```

Pipx can also let you run IGA directly using `pipx run iga`, although in that case, you must always prefix every IGA command with `pipx run`.  Consult the [documentation for `pipx run`](https://github.com/pypa/pipx#walkthrough-running-an-application-in-a-temporary-virtual-environment) for more information.


### _Alternative 2: installing IGA using `pip`_

You should be able to install `iga` with [`pip`](https://pip.pypa.io/en/stable/installing/) for Python&nbsp;3.  To install `iga` from the [Python package repository (PyPI)](https://pypi.org), run the following command:
```sh
python3 -m pip install iga
```

As an alternative to getting it from [PyPI](https://pypi.org), you can use `pip` to install `iga` directly from GitHub:
```sh
python3 -m pip install git+https://github.com/caltechlibrary/iga.git
```

_If you already installed IGA once before_, and want to update to the latest version, add `--upgrade` to the end of either command line above.


### _Alternative 3: installing IGA from sources_

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


## Usage

IGA creates a metadata record in an InvenioRDM server and attaches a GitHub release archive to the record. The GitHub release can be specified using _either_ a full release URL, _or_ a combination of GitHub account + repository + tag. Different command-line options can be used to adjust this behavior.

If the installation process described above is successful, you should end up with a program named `iga` in a location where software is normally installed on your computer.  Running `iga` should be as simple as running any other command-line program. For example, the following command should print a helpful message to your terminal:
```shell
iga --help
```

### Specification of the InvenioRDM server and access token

The server address must be provided either as the value of the option `--invenio-server` or in an environment variable named `INVENIO_SERVER`.  If the server address does not begin with `https://`, IGA will prepended it automatically.

A Personal Access Token (PAT) for making API calls to the InvenioRDM server must be also supplied when invoking IGA. The preferred method is to set the value of the environment variable `INVENIO_TOKEN`. Alternatively, you can use the option `--invenio-token` to pass the token on the command line, but **you are strongly advised to avoid this practice because it is insecure**.  To obtain a PAT from an InvenioRDM server, first log in to the server, then visit the page at `/account/settings/applications` and use the interface there to create a token.

### Specification of a GitHub release

A GitHub release can be specified to IGA in one of two mutually-exclusive ways:
 1. The full URL of the web page on GitHub of a tagged release. In this case,
    the URL must be the final argument on the command line invocation of IGA
    and the options `--account` and `--repo` must be omitted.
 2. A combination of _account name_, _repository name_, and _tag_. In this
    case, the final argument on the command line must be the _tag_, and in
    addition, values for the options `--account` and `--repo` must be provided.

Here's an example using approach #1 (assuming environment variables `INVENIO_SERVER`, `INVENIO_TOKEN`, and `GITHUB_TOKEN` have all been set):
```shell
iga https://github.com/mhucka/taupe/releases/tag/v1.2.0
```
and here's the equivalent using approach #2:
```shell
iga --github-account mhucka --github-repo taupe v1.2.0
```
Note that when using this form of the command, the release tag (`v1.2.0` above) must be the last item given on the command line.

### Use of a GitHub access token

It is possible to run IGA without providing a GitHub access token. GitHub allows up to 60 API calls per minute when running without credentials, and though IGA makes several API calls to GitHub each time it runs, for many repositories, IGA will not hit the limit. However, if you run IGA multiple times in a row or your repository has many contributors, then you may need to supply a GitHub access token. The preferred way of doing that is to set the value of the environment variable `GITHUB_TOKEN`. Alternatively, you can use the option `--github-token` to pass the token on the command line, but **you are strongly advised to avoid this practice because it is insecure**.  To obtain a PAT from GitHub, visit https://docs.github.com/en/authentication and follow the instructions for creating a "classic" personal access token.

### Construction of an InvenioRDM record

The record created in InvenioRDM is constructed using information obtained using GitHub's API as well as several other APIs as needed. The information includes the following:
 * (if one exists) a `codemeta.json` file in the GitHub repository
 * (if one exists) a `CITATION.cff` file in the GitHub repository
 * data available from GitHub for the release
 * data available from GitHub for the repository
 * data available from GitHub for the account of the owner
 * data available from GitHub for the accounts of repository contributors
 * file assets associated with the GitHub release
 * data available from ORCID.org for ORCID identifiers
 * data available from ROR.org for Research Organization Registry identifiers
 * data available from DOI.org, NCBI, Google Books, & others for publications
 * data available from spdx.org for software licenses

IGA tries to use `CodeMeta.json` first and `CITATION.cff` second to fill out the fields of the InvenioRDM record. If neither of those files are present, IGA uses values from the GitHub repository instead. You can make it always use all sources of info with the option `--all-metadata`. Depending on how complete and up-to-date your `CodeMeta.json` and `CITATION.cff` are, this may or may not make the record more comprehensive and may or may not introduce redundancies or unwanted values.

To override the auto-created record, use the option `--read-record` followed by the path to a JSON file structured according to the InvenioRDM schema used by the destination server. When `--read-record` is provided, IGA does _not_ extract the data above, but still obtains the file assets from GitHub.

### Specification of GitHub file assets

By default, IGA attaches to the InvenioRDM record _only_ the ZIP file asset created by GitHub for the release. To make IGA attach all assets associated with the GitHub release, use the option `--all-assets`.

To upload specific file assets and override the default selections made by IGA, you can use the option `--file` followed by a path to a file to be uploaded.  You can repeat the option `--file` to upload multiple file assets. Note that if `--file` is provided, then IGA _does not use any file assets from GitHub_; it is the user's responsibility to supply all the files that should be uploaded.

If both `--read-record` and `--file` are used, then IGA does not actually contact GitHub for any information.

### Handling communities

To submit your record to a community, use the `--community` option together with a community name. The option `--list-communities` can be used to get a list of communities supported by the InvenioRDM server. Note that submitting a record to a community means that the record will not be finalized and will not be publicly visible when IGA finishes; instead, the record URL that you receive will be for a draft version, pending review by the community moderators.

### Draft versus published records

If the `--community` option is not used, then by default, IGA will finalize and publish the record. To make it stop short and leave the record as a draft instead, use the option `--draft`. The draft option also takes precedence over the community option: if you use both `--draft` and `--community`, IGA will stop after creating the draft record and will _not_ submit it to the community.  (You can nevertheless submit the record to a community manually once the draft is created, by visiting the record's web page and using the InvenioRDM interface there.)

### Other options recognized by IGA

Running IGA with the option `--save-record` will make it create a metadata record, but instead of uploading the record (and any assets) to the InvenioRDM server, IGA will write the result to the given destination. This can be useful not only for debugging but also for creating a starting point for a custom metadata record: first run IGA with `--save-record` to save a record to a file, edit the result, then finally run IGA with the `--read-record` option to use the modified record to create a release in the InvenioRDM server.

The `--mode` option can be used to change the run mode. Four run modes are available: `quiet`, `normal`, `verbose`, and `debug`. The default mode is `normal`, in which IGA prints a few messages while it's working. The mode `quiet` will make it avoid printing anything unless an error occurs, the mode `verbose` will make it print a detailed trace of what it is doing, and the mode `debug` will make IGA even more verbose. In addition, in `debug` mode, IGA will drop into the `pdb` debugger if it encounters an exception during execution. On Linux and macOS, debug mode also installs a signal handler on signal USR1 that causes IGA to drop into the `pdb` debugger if the signal USR1 is received. (Use `kill -USR1 NNN`, where NNN is the IGA process id.)

Networks latencies are unpredicatable. Reading and writing large files may take a long time; on the other hand, IGA should not wait forever before reporting an error if a server or network becomes unresponsive. To balance these conflicting needs, IGA automatically scales its network timeout based on file sizes. To override its adaptive algorithm and set an explicit timeout value, use the option `--timeout` with a value in seconds.

By default, the output of the `verbose` and `debug` run modes is sent to the standard output (normally the terminal console). The option `--log-dest` can be used to send the output to the given destination instead. The value can be `-` to indicate console output, or a file path to send the output to the file.

If given the `--version` option, this program will print its version and other information, and exit without doing anything else.

Running IGA with the option `--help` will make it print help text and exit without doing anything else.


### Summary of command-line options

As explain above, IGA takes one required argument on the command line: either (1) the full URL of a web page on GitHub of a tagged release, or (2) a release tag name which is to be used in combination with options `--github-account` and `--github-repo`. The following table summarizes all the command line options available.

| Long&nbsp;form&nbsp;option&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Short&nbsp;&nbsp; | Meaning | Default |  |
|------------------------|----------|--------------------------------------|---------|---|
| `--all-assets`         | `-A`     | Attach all GitHub assets | Attach only the release source ZIP| |
| `--all-metadata`       | `-M`     | Include additional metadata from GitHub | Favor CodeMeta & CFF | |
| `--community` _C_      | `-c` _C_ | Submit record to RDM community _C_ | Don't submit record to any community | | 
| `--draft`              | `-d`     | Mark the RDM record as a draft | Publish record when done | |
| `--file` _F_           | `-f` _F_ | Upload local file _F_ instead of GitHub assets | Upload only GitHub assets | ⚑ |
| `--github-account` _A_ | `-a` _A_ | Look in GitHub account _A_ | Get account name from release URL | ✯ | 
| `--github-repo` _R_    | `-r` _R_ | Look in GitHub repository _R_ of account _A_ | Get repo name from release URL | ✯ |
| `--github-token` _T_   | `-t` _T_ | Use GitHub acccess token _T_| Use value in env. var. `GITHUB_TOKEN` | |
| `--help`               | `-h`     | Print help info and exit | | |
| `--invenio-server` _S_ | `-s` _S_ | Send record to InvenioRDM server at address _S_ | Use value in env. var. `INVENIO_SERVER` | | 
| `--invenio-token` _K_  | `-k` _K_ | Use InvenioRDM access token _K_ | Use value in env. var. `INVENIO_TOKEN` | | 
| `--list-communities`   | `-L`     | List communities available for use with `--community` | | |
| `--log-dest` _L_       | `-l` _L_ | Write log output to destination _L_ | Write to terminal | ⚐ |
| `--mode` _M_           | `-m` _M_ | Run in mode `quiet`, `normal`, `verbose`, or `debug` | `normal` | |
| `--open`               | `-O`     | Open record's RDM web page in a browser when done | Do nothing when done | |
| `--read-record` _R_    | `-R` _R_ | Read metadata record from _R_; don\'t build one | Build metadata record | |
| `--save-record` _D_    | `-S` _D_ | Save metadata record to _D_; don\'t upload it | Upload to InvenioRDM server | |
| `--timeout` _X_        | `-T` _X_ | Wait on network operations a max of _X_ seconds | Auto-adjusted based on file size | |
| `--version`            | `-V`     | Print program version info and exit | | |

⚑ &nbsp; Can repeat for multiple files.<br>
⚐ &nbsp; To write to the console, use the character `-` as the value of _OUT_; otherwise, _OUT_ must be the name of a file where the output should be written.<br>
✯ &nbsp; When using `--github-account` and `--github-repo`, the last argument on the command line must be a release tag name.

### Return values

This program exits with a return status code of 0 if no problem is encountered.  Otherwise, it returns a nonzero status code. The following table lists the possible values:

| Code | Meaning                                                  |
|:----:|----------------------------------------------------------|
| 0    | success &ndash; program completed normally               |
| 1    | interrupted                                              |
| 2    | encountered a bad or missing value for an option         |
| 3    | encountered a problem with a file or directory           |
| 4    | encountered a problem interacting with GitHub            |
| 5    | encountered a problem interacting with InvenioRDM        |
| 6    | an exception or fatal error occurred                     |


## Known issues and limitations

_[… forthcoming …]_

## Getting help

If you find an issue, please submit it in [the GitHub issue tracker](https://github.com/caltechlibrary/iga/issues) for this repository.


## Contributing

Your help and participation in enhancing IGA is welcome!  Please visit the [guidelines for contributing](CONTRIBUTING.md) for some tips on getting started.


## License

Software produced by the Caltech Library is Copyright © 2023 California Institute of Technology.  This software is freely distributed under a BSD-style license.  Please see the [LICENSE](LICENSE) file for more information.

## Acknowledgments

This work was funded by the California Institute of Technology Library.

IGA uses multiple other open-source packages, without which it would have taken much longer to write the software. I want to acknowledge this debt. In alphabetical order, the packages are:
* [Aenum](https://github.com/ethanfurman/aenum) &ndash; package for advanced enumerations
* [Arrow](https://pypi.org/project/arrow/) &ndash; a library for creating & manipulating dates
* [Boltons](https://github.com/mahmoud/boltons/) &ndash; package of miscellaneous Python utilities
* [caltechdata_api](https://github.com/caltechlibrary/caltechdata_api) &ndash; package for using the CaltechDATA API
* [CommonPy](https://github.com/caltechlibrary/commonpy) &ndash; a collection of commonly-useful Python functions
* [demoji](https://github.com/bsolomon1124/demoji) &ndash; find or remove emojis from text
* [dirtyjson](https://github.com/codecobblers/dirtyjson) &ndash; JSON decoder that copes with problematic JSON files and reports useful error messages
* [flake8](https://github.com/pycqa/flake8) &ndash; Python code linter and style analyzer
* [httpx](https://www.python-httpx.org) &ndash; HTTP client library that supports HTTP/2
* [humanize](https://github.com/jmoiron/humanize) &ndash; make numbers more easily readable by humans
* [idutils](https://github.com/inveniosoftware/idutils) &ndash; package for validating and normalizing various kinds of persistent identifiers
* [ipdb](https://github.com/gotcha/ipdb) &ndash; the IPython debugger
* [iptools](https://github.com/bd808/python-iptools) &ndash; utilities for dealing with IP addresses
* [isbnlib](https://github.com/xlcnd/isbnlib) &ndash; utilities for dealing with ISBNs
* [json5](https://github.com/dpranke/pyjson5) &ndash; extended JSON format parser
* [latexcodec](https://github.com/mcmtroffaes/latexcodec) &ndash; lexer and codec to work with LaTeX code in Python
* [lxml](https://lxml.de) &ndash; an XML parsing library
* [Markdown](https://python-markdown.github.io) &ndash; Python package for working with Markdown
* [markdown-checklist](https://github.com/FND/markdown-checklist) &ndash; GitHub-style checklist extension for Python Markdown package
* [mdx-breakless-lists](https://github.com/adamb70/mdx-breakless-lists) &ndash; GitHub-style Markdown lists that don't require a line break above them
* [mdx_linkify](https://github.com/daGrevis/mdx_linkify) &ndash; extension for Python Markdown will convert text that look like links to HTML anchors
* [nameparser](https://github.com/derek73/python-nameparser) &ndash; package for parsing human names into their individual components
* [probablepeople](https://github.com/datamade/probablepeople) &ndash; package for parsing names into components using ML-based techniques
* [pymdown-extensions](https://github.com/facelessuser/pymdown-extensions) &ndash; extensions for Python Markdown
* [PyYAML](https://pyyaml.org) &ndash; YAML parser
* [pybtex](https://pybtex.org) &ndash; BibTeX parser and formatter
* [pybtex-apa7-style]() &ndash; plugin for [pybtex](https://pybtex.org) that provides APA7 style formatting
* [pytest](https://docs.pytest.org/en/stable/) &ndash; testing framework
* [pytest-cov](https://github.com/pytest-dev/pytest-cov) &ndash; coverage reports for use with `pytest`
* [pytest-mock](https://pypi.org/project/pytest-mock/) &ndash; wrapper around the `mock` package for use with `pytest`
* [Rich](https://github.com/Textualize/rich) &ndash; library for writing styled text to the terminal
* [rich-click](https://github.com/ewels/rich-click) &ndash; CLI interface built on top of [Rich](https://github.com/Textualize/rich)
* [Sidetrack](https://github.com/caltechlibrary/sidetrack) &ndash; simple debug logging/tracing package
* [spaCy](https://spacy.io) &ndash; Natural Language Processing package
* [spacy-alignments](https://github.com/explosion/spacy-alignments) &ndash; alternate alignments for [spaCy](https://spacy.io)
* [spacy-legacy](https://pypi.org/project/spacy-legacy/) &ndash; [spaCy](https://spacy.io) legacy functions and architectures for backwards compatibility
* [spacy-loggers](https://github.com/explosion/spacy-loggers) &ndash; loggers for [spaCy](https://spacy.io)
* [spacy-pkuseg](https://github.com/explosion/spacy-pkuseg) &ndash; Chinese word segmentation toolkit for [spaCy](https://spacy.io)
* [spacy-transformers](https://spacy.io) &ndash; pretrained Transformers for [spaCy](https://spacy.io)
* [setuptools](https://github.com/pypa/setuptools) &ndash; library for `setup.py`
* [StringDist](https://github.com/obulkin/string-dist) &ndash; library for calculating string distances
* [Twine](https://github.com/pypa/twine) &ndash; utilities for publishing Python packages on [PyPI](https://pypi.org)
* [url-normalize](https://github.com/niksite/url-normalize) &ndash; URI/URL normalization utilities
* [validators](https://github.com/kvesteri/validators) &ndash; data validation package for Python
* [wheel](https://pypi.org/project/wheel/) &ndash; setuptools extension for building wheels

<div align="center">
  <br>
  <a href="https://www.caltech.edu">
    <img width="100" height="100" src="https://github.com/caltechlibrary/iga/blob/main/.graphics/caltech-round.png">
  </a>
</div>
