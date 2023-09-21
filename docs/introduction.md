# Introduction

[InvenioRDM](https://inveniosoftware.org/products/rdm/) is a research data management (RDM) repository platform based on the [Invenio Framework](https://inveniosoftware.org/products/framework/) and [Zenodo](https://www.zenodo.org). At institutions like Caltech, InvenioRDM is used as the basis for institutional repositories such as [CaltechDATA](https://data.caltech.edu). It offers the means to preserve software and data projects in a long-term archive managed by their institution.

<figure>
    <img src="_static/media/example-record-landing-page.jpg" width="80%">
    <figcaption>Screenshot of a landing page for a record in <a href="https://data.caltech.edu">CaltechDATA</a>. The source code for version 1.3.5 of the software project <a href="https://data.caltech.edu/records/fqmae-krq60">eprints2archives</a> has been archived in the repository, and this example shows some of the metadata associated with that archived copy.</figcaption>
</figure>

The metadata contained in the record of a deposit is critical to making the record widely discoverable by other people, but it can be tedious and error-prone to enter the metadata by hand.  This is where automation such as IGA come in: _IGA can save users the trouble of depositing software and filling out the metadata record in InvenioRDM by performing all the steps automatically._

## IGA features

The _InvenioRDM GitHub Archiver_ (IGA) creates metadata records and sends [software releases from GitHub](https://docs.github.com/en/repositories/releasing-projects-on-github/about-releases) to an InvenioRDM-based repository server. IGA can be invoked from the command line; it also can be set up as a [GitHub Action](https://docs.github.com/en/actions) to archive GitHub releases automatically in an InvenioRDM repository. Here are some of IGA's other notable features:
* Automatic metadata extraction from GitHub releases, repositories, and [`codemeta.json`](https://codemeta.github.io) and [`CITATION.cff`](https://citation-file-format.github.io) files
* Thorough coverage of [InvenioRDM record metadata](https://inveniordm.docs.cern.ch/reference/metadata) using painstaking procedures
* Recognition of identifiers that appear in CodeMeta and CFF files, including [ORCID](https://orcid.org), [ROR](https://ror.org), [DOI](https://www.doi.org), [arXiv](https://arxiv.org), and [PMCID](https://www.ncbi.nlm.nih.gov/pmc/about/public-access-info/)
* Automatic lookup of publication data in [DOI.org](https://www.doi.org), [PubMed]((https://www.ncbi.nlm.nih.gov/pmc/about/public-access-info/)), Google Books, & other sources if needed
* Automatic lookup of organization names in [ROR](https://ror.org) (assuming ROR id's are provided)
* Automatic lookup of human names in [ORCID.org](https://orcid.org) if needed (assuming ORCID id's are provided)
* Automatic splitting of human names into family and given names using [ML](https://en.wikipedia.org/wiki/Machine_learning)-based methods if necessary
* Support for InvenioRDM [communities](https://invenio-communities.readthedocs.io/en/latest/)
* Support for overriding the metadata record it creates, for complete control if you need it
* Ability to use the GitHub API without a [GitHub access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) in many cases
* Extensive use of logging so you can see what's going on under the hood


## GitHub releases

Although IGA can be used to produce arbitrary records in InvenioRDM repositories, it's focused on automating the process of creating records for GitHub releases.

A [_release_ in GitHub](https://github.blog/2013-07-02-release-your-software/) is the mechanism by which users can package up a specific version of their software or data in a way that makes it easy for other users to obtain a copy. Releases are associated with individual repositories and are identified by [git tags](https://git-scm.com/book/en/v2/Git-Basics-Tagging); they can contain source code archives (e.g., in [ZIP](https://en.wikipedia.org/wiki/ZIP_(file_format)) format), release notes, and binary assets such as compiled executables. Below is the GitHub release page for the record shown in the previous figure.

<figure>
    <img src="_static/media/example-github-release.jpg">
    <figcaption>The page in GitHub describing the release shown archived in InvenioRDM in the previous figure.</figcaption>
</figure>

You may be asking yourself "but … if the releases are already stored in GitHub, why bother storing them elsewhere?" There are at least two reasons:
1. GitHub is not an archive. Repositories can be renamed or deleted (intentionally or accidentally), and so can user accounts; moreover, the contents of releases can also be edited and changed. In other words, _what is available on GitHub today may not be available there tomorrow_. Preservation of digital contents needs an archiving approach capable of retaining immutable copies of software in a form that can outlive individual projects and people.
2. Compliance with open data requirements. Many funding agencies and institutions require that research projects ensure free access to products of the research. Institutional repositories are specifically designed to support the needs of researchers in complying with funder or publisher data requirements. _Institutional repositories provide features that GitHub does not_, such as assigning globally-unique, _permanent_, citable identifiers (such as [DOI](https://en.wikipedia.org/wiki/Digital_object_identifier)s) for data and software.


## CodeMeta & CITATION.cff

GitHub by itself only records relatively sparse metadata about software releases and users associated with them. Thankfully, two efforts in recent years provide the means for software authors to describe software projects in more detail: [CodeMeta](https://codemeta.github.io) and [CITATION.cff](https://citation-file-format.github.io). Both are becoming increasingly well-known, especially among research software developers. Tips for creating them can be found in [a separate section](tips.md#how-do-you-create-them) of this document.

IGA looks for `codemeta.json` and `CITATION.cff` files in a repository and uses the information in them as the primary bases for constructing InvenioRDM metadata records. If a repository contains neither file, IGA resorts to using only the metadata provided by GitHub for the release and the associated repository.


## Using IGA

IGA makes it easy to archive any release from GitHub into an InvenioRDM server. Once you have a personal access token ([PAT](glossary.md#term-PAT)) for InvenioRDM (and optionally, one for GitHub too) and have set the environment variable `INVENIO_TOKEN` (and optionally `GITHUB_TOKEN`), you can archive a GitHub release as easily as in this example:
```shell
iga -s data.caltech.edu https://github.com/mhucka/taupe/releases/tag/v1.2.0
```
IGA will contact GitHub, extract metadata from the release and the repository, construct a metadata record in the format required by InvenioRDM, and send the record plus the GitHub release source archive (a [ZIP](https://en.wikipedia.org/wiki/ZIP_(file_format)) file) to the InvenioRDM server. Various options can modify IGA's behavior, as explained in detail in the section on [command-line usage of IGA](cli-usage.md).

Note that the availability of a command-line version of IGA means you can also use it to send _past_ GitHub releases to an InvenioRDM server &ndash; IGA doesn't care if what you're asking it to archive is the _latest_ release of something; it can archive any release. This makes it useful for archiving past projects; it also makes it possible for institutions to easily perform activities such as archiving software on behalf of faculty and students.

As a GitHub Action, IGA allows you to set up a GitHub workflow that will automatically send new releases to a designated InvenioRDM server. The procedure for this is detailed in the section on [GitHub Action usage of IGA](gha-usage.md). Once set up, you do not have to remember to send releases of a particular GitHub project to InvenioRDM &ndash; it will do it for you.
