# Getting the most out of IGA

Data and software archived in a repository need to be described thoroughly and richly cross-referenced in order to be widely discoverable by other people. As mentioned in the section on [metadata sources](cli-usage.md#metadata-sources), IGA by default constructs a metadata record using information it gathers from the software release, the GitHub repository, the GitHub API, and various other APIs as needed. This section provides more information about that process and offers guidance for how to help IGA produce good metadata.


## Use CodeMeta or CFF files?

Should you use one or the other, or both? The answer turns out to be: _use both_. They don't overlap completely in their content, they serve different purposes, and they are used differently by different software tools.

The purpose of a [`CITATION.cff`](https://citation-file-format.github.io) is to let others know how to correctly cite your software or dataset. GitHub makes use of `CITATION.cff` files: when you put a `CITATION.cff` file in the default branch of your repository, [GitHub automatically creates a link](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-citation-files) labeled _Cite this repository_ in the right sidebar of the repository landing page. Here is an example:

<figure>
    <img src="_static/media/example-github-citation.jpg" width="50%">
    <figcaption>When GitHub detects a <code>CITATION.cff</code> file in the default branch of a repository, it adds a "<em>Cite this repository</em>" menu item in the right-hand sidebar. Clicking the item reveals information about how to cite the software.</figcaption>
</figure>

Conversely, a [`codemeta.json`](https://codemeta.github.io) file is a way to describe a software project in machine readable form, for purposes of discovery, indexing, preservation, reuse, and attribution. It is thus more general and somewhat more comprehensive than a `CITATION.ff` file.


## Which is more important?

IGA relies most on the `codemeta.json` file. It considers information sources in the following order:
1. The metadata provided by GitHub for a release is used as the primary source of metadata for certain information that is tightly coupled to the release, namely the description of the release and the version tag name.
2. Provided that a `codemeta.json` file exists in the repository and the relevant data fields are present in the file, it is used as the primary source for all other metadata, except for metadata that is _only_ defined in `CITATION.cff` or the GitHub repository. (In particular, the resource type -- software versus dataset -- is _only_ defined in a `CITATION.cff` field, and the role of "contact" is only explicitly defined in the `CITATION.cff` format.)
3. Provided that a `CITATION.cff` file exists in the repository and the relevant data fields are present in the file, it is used as a secondary source of metadata if there is no `codemeta.json` in the repository or it lacks certain fields. (It is also the primary source for a couple of fields that have no equivalent anywhere else, as noted above.)
4. The metadata provided by GitHub for the repository is used as a tertiary source of information if neither `codemeta.json` nor `CITATION.cff` files are provided, or IGA is invoked with the flag `--all-metadata`. (See the section on [Usage](cli-usage.md).)

A detailed mapping of how IGA uses `codemeta.json`, `CITATION.cff`, and GitHub repository and release data is given in the [Appendix](appendix-metadata.md). 


## What if you have neither?

If the repository you are archiving has neither a `codemeta.json` nor a `CITATION.cff` file, IGA will automatically act as if the `--all-metadata` option is being used. This helps produce a more complete InvenioRDM record, and while the result will not be as comprehensive as if a repository has a `codemeta.json` or at least a `CITATION.cff` file, it will be better than nothing.


## How do you create them?

`codemeta.json` and `CITATION.cff` files are text files, and can be written by hand in a text editor. However, `codemeta.json` is more difficult to write by hand becasue of the JSON-LD syntax it uses, and in both cases, it is easier if you can use a software tool to generate the files. Here are some options available at this time:
* The main [CodeMeta generator](https://codemeta.github.io/codemeta-generator/)
* The [codemetar](https://cran.r-project.org/web/packages/codemetar/) package for R
* The [CodeMetaPy](https://pypi.org/project/CodeMetaPy/) package for Python
* The [CFFINIT](https://citation-file-format.github.io/cff-initializer-javascript/#/) online tool for `CITATION.cff`
