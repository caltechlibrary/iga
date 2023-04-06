# Introduction

[InvenioRDM](https://inveniosoftware.org/products/rdm/) is a research data management (RDM) repository platform based on [Invenio Framework](https://inveniosoftware.org/products/framework/) and [Zenodo](https://www.zenodo.org). At institutions like Caltech, InvenioRDM is used as the basis for institutional data and software repositories such as [CaltechDATA](https://data.caltech.edu). Of particular interest to software developers is that a repository like [CaltechDATA](https://data.caltech.edu) offers the means to preserve software projects in a long-term archive managed by their institution.

The _InvenioRDM GitHub Archiver_ (IGA) is a tool for sending software releases from GitHub to an InvenioRDM-based repository server. IGA can be invoked from the command line to send releases on demand; it also can be set up as a [GitHub Action](https://docs.github.com/en/actions) to automate the archiving of GitHub software releases in an InvenioRDM repository. Here are some of IGA's other notable features:
* Automatic extraction of metadata from the GitHub release, the GitHub repository, and [`codemeta.json`](https://codemeta.github.io) and/or [`CITATION.cff`](https://citation-file-format.github.io) files if they exist in the repository
* Thorough coverage of [InvenioRDM record metadata](https://inveniordm.docs.cern.ch/reference/metadata) using painstaking procedures
* Automatic recognition of common identifier types that often appear CodeMeta and CFF files, such as [ORCID](https://orcid.org), [ROR](https://ror.org), [DOI](https://www.doi.org), [arXiV](https://arxiv.org), [PMCID/PMID](https://www.ncbi.nlm.nih.gov/pmc/about/public-access-info/), and others
* Automatic lookup of human names in [ORCID.org](https://orcid.org) if needed (assuming ORCID id's are provided)
* Automatic lookup of organization names in [ROR](https://ror.org) (assuming ROR id's are provided)
* Automatic lookup of publication data in [DOI.org](https://www.doi.org), [PubMed]((https://www.ncbi.nlm.nih.gov/pmc/about/public-access-info/)), Google Books, & other sources if needed
* Automatic splitting of human names into family and given names using [ML](https://en.wikipedia.org/wiki/Machine_learning)-based methods, if necessary, to comply with InvenioRDM requirements
* Support for overriding the metadata it record it creates, for complete control if you need it
* Support for InvenioRDM [communities](https://invenio-communities.readthedocs.io/en/latest/)
* Ability to use the GitHub API without a [GitHub access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) in many cases
* Extensive use of logging so you can see what's going on under the hood


## InvenioRDM records

[Research Data Management](https://riojournal.com/article/56508/) (RDM) refers to the organization, storage, preservation, and sharing of data and software that is created, collected, and used in a research project. [InvenioRDM](https://inveniordm.docs.cern.ch) is a turn-key RDM platform that can be used by institutions to create repositories where data and software can be stored in order ensure long-term access to research products. Institutions such as Caltech use InvenioRDM as the basis for institutional data repositories. [CaltechDATA](https://data.caltech.edu) is an example of an InvenioRDM-based repository; it enables researchers to upload research data and software, link data with their publications, and assign permanent [DOI](https://en.wikipedia.org/wiki/Digital_object_identifier)s to them so that other people can reference them.

Data and software archived in a repository need to be described well and richly cross-referenced in order to be widely discoverable by other people. The metadata records needed by InvenioRDM are expressed in a common file format ([JSON](https://www.json.org)), with required metadata fields [defined by InvenioRDM](https://inveniordm.docs.cern.ch/reference/metadata/). The record fields store information about the creators of the software (or data), distribution rights, titles, funding sources, publications, and more; InvenioRDM formats the metadata records as attractive web pages for human consumption. To give an example, below is a screenshot of the page for a software project stored in [CaltechDATA](https://data.caltech.edu):

<figure>
    <img src="_static/media/example-record-landing-page.jpg">
    <figcaption>Example of a landing page for a record in CaltechDATA.</figcaption>
</figure>

The nice features come at a price: the metadata contained in the record of a deposit can be tedious and error-prone to fill out by hand.  This is where automation such as IGA come in: _IGA can save users the trouble of depositing software and filling out the metadata record in InvenioRDM by performing all the steps automatically._


## GitHub releases

Although IGA can be used to produce arbitrary records in InvenioRDM repositories, it's focused on automating the process of creating records for GitHub software releases.

A [_release_ in GitHub](https://github.blog/2013-07-02-release-your-software/) is the mechanism by which users can package up a specific version of their software in a way that makes it easy for other users to obtain a copy. Releases are associated with individual repositories and are identified by [git tags](https://git-scm.com/book/en/v2/Git-Basics-Tagging); they can contain source code archives (e.g., in [ZIP](https://en.wikipedia.org/wiki/ZIP_(file_format)) format), release notes, and binary assets such as compiled executables.

You may wonder, why would you bother saving GitHub releases anywhere else if they're already stored on GitHub? There are at least two reasons:
1. GitHub is not an archive. Repositories can be renamed or deleted (intentionally or accidentally), as can user accounts; moreover, the contents of releases can also be edited and changed. In other words, _what is available on GitHub today may not be available there tomorrow_. Preservation of software products demands an archiving approach capable of retaining immutable copies of software in a form that can outlive individual projects and people.
2. Compliance with open data requirements. Many funding agencies and institutions require that research projects ensure free access to research products. Institutional repositories are specifically designed to support the needs of researchers in complying with funder or publisher data requirements. _They provide features that GitHub does not_, such as assigning globally-unique, _permanent_, citable identifiers (such as [DOI](https://en.wikipedia.org/wiki/Digital_object_identifier)s) for data and software.


## CodeMeta and CITATION.cff

GitHub by itself only records relatively sparse metadata about software releases and users associated with them. Thankfully, two efforts in recent years provide the means for software authors to describe software projects in more detail: [CodeMeta](https://codemeta.github.io) and [CITATION.cff](https://citation-file-format.github.io). Both are becoming increasingly well-known, especially among research software developers.

IGA looks for `codemeta.json` and `CITATION.cff` files in a repository and uses the information found therein as the primary bases for constructing InvenioRDM metadata records. If a repository contains neither file, IGA resorts to using only the metadata provided by GitHub for the release and the associated repository. (You can also opt to make IGA add the metadata from GitHub even if it does find one or both of the `codemeta.json` and `CITATION.cff` files repository; this may or may not result in a richer metadata record, depending on how complete the CodeMeta and/or CFF files are, but it can also produce more duplicate or unwanted values, which is why the default in IGA is to focus on the CodeMeta and CFF files.)
