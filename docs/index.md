# InvenioRDM GitHub Archiver<img width="50em" align="right" style="display: block; margin: auto auto 2em 2em"  src="_static/media/cloud-upload.svg">

[InvenioRDM](https://inveniosoftware.org/products/rdm/) is the basis for many institutional repositories such as [CaltechDATA](https://data.caltech.edu) that enable users to preserve software and datasets in long-term archive. Though such repositories are critical resources, creating detailed records and uploading assets can be a tedious and error-prone process if done manually. This is where the [_InvenioRDM GitHub Archiver_](https://github.com/caltechlibrary/iga) (IGA) comes in.

IGA creates metadata records and sends releases from GitHub to an InvenioRDM-based repository server. IGA can be invoked from the command line; it also can be set up as a [GitHub Action](https://docs.github.com/en/actions) to archive GitHub releases automatically for a repository each time they are made.

<figure>
<img align="middle" src="https://github.com/caltechlibrary/iga/raw/main/docs/_static/media/example-github-release.jpg" width="40%">
<span style="font-size: 150%">➜</span>
<img align="middle" src="https://github.com/caltechlibrary/iga/raw/main/docs/_static/media/example-record-landing-page.jpg" width="40%">
    <figcaption>IGA sends metadata and assets from GitHub to an InvenioRDM server..</figcaption>
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
appendix-metadata.md
```
