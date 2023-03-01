# IGA<img width="12%" align="right" src="https://github.com/caltechlibrary/iga/raw/main/docs/_static/media/cloud-upload.png">

IGA is the _InvenioRDM GitHub Archiver_, a standalone program as well as a GitHub Action that lets you automatically archive GitHub software releases in an [InvenioRDM](https://inveniosoftware.org/products/rdm/) repository.

[![License](https://img.shields.io/badge/License-BSD--like-lightgrey.svg?style=flat-square)](https://github.com/caltechlibrary/iga/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-brightgreen.svg?style=flat-square)](https://www.python.org/downloads/release/python-380/)
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

[InvenioRDM](https://inveniosoftware.org/products/rdm/) is a research data management (RDM) repository platform based on [Invenio Framework](https://inveniosoftware.org/products/framework/) and [Zenodo](https://www.zenodo.org). At institutions like Caltech, InvenioRDM is used as the basis for institutional data and software repositories such as [CaltechDATA](https://data.caltech.edu). Of particular interest to software developers is that a repository like [CaltechDATA](https://data.caltech.edu) offers the means to preserve software projects in a long-term archive managed by their institution.

The _InvenioRDM GitHub Archiver_ (IGA) is a tool for sending software releases from GitHub to an InvenioRDM-based repository server. IGA can be invoked from the command line to send releases on demand; it also can be set up as a [GitHub Action](https://docs.github.com/en/actions) to automate the archiving of GitHub software releases in an InvenioRDM repository. Here are some of IGA's other notable features:
* Automatic extraction of metadata from the GitHub release, the GitHub repository, and [`codemeta.json`](https://codemeta.github.io) and/or [`CITATION.cff`](https://citation-file-format.github.io) files if they exist in the repository
* Automatic recognition of common identifier types that often appear CodeMeta and CFF files, such as [ORCID](https://orcid.org), [ROR](https://ror.org), [DOI](https://www.doi.org), [arXiV](https://arxiv.org), [PMCID/PMID](https://www.ncbi.nlm.nih.gov/pmc/about/public-access-info/), and others
* Thorough coverage of [InvenioRDM record metadata](https://inveniordm.docs.cern.ch/reference/metadata) using painstaking procedures
* Support for overriding the metadata it record it creates, for complete control if you need it
* Use of the GitHub API without the need for a [GitHub access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) in most cases
* Extensive use of logging so you can see what's going on under the hood


## Installation

_[… forthcoming …]_ 

## Usage

_[… forthcoming …]_

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

<div align="center">
  <br>
  <a href="https://www.caltech.edu">
    <img width="100" height="100" src="https://github.com/caltechlibrary/iga/blob/main/.graphics/caltech-round.png">
  </a>
</div>
