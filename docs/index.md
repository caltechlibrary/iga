# InvenioRDM GitHub Archiver<img width="50em" align="right" style="display: block; margin: auto auto 2em 2em"  src="_static/media/cloud-upload.svg">

[InvenioRDM](https://inveniosoftware.org/products/rdm/) is used by many institutional repositories such as [CaltechDATA](https://data.caltech.edu) to let users preserve software and data in a long-term archive managed by their institution. Depositing software and/or data into these repositories requires the creation of detailed metadata records &ndash; a tedious and error-prone process if done manually. This is where the [_InvenioRDM GitHub Archiver_](https://github.com/caltechlibrary/iga) (IGA) comes in.

IGA can create metadata records and send releases from GitHub to an InvenioRDM-based repository server. It can be run as a command line program; it also can be set up as a [GitHub Action](https://docs.github.com/en/actions) to archive GitHub releases in InvenioRDM automatically each time they are made.

<figure>
<img align="middle" src="_static/media/example-github-release.jpg" width="40%">
<span style="font-size: 150%">➜</span>
<img align="middle" src="_static/media/example-record-landing-page.jpg" width="40%">
    <figcaption>IGA sends metadata and assets from GitHub to an InvenioRDM server.</figcaption>
</figure>


## Sections

```{toctree}
---
maxdepth: 2
---
introduction.md
installation.md
quick-start.md
cli-usage.md
gha-usage.md
tips.md
glossary.md
colophon.md
appendix.md
```
