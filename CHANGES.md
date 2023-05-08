# Change log for IGA

## Version 0.0.9 (TBD)

Changes in this release:
* `IGA` and `GitHub` are now added automatically to the list of subject tags in the InvenioRDM record created by IGA.
* Debug mode will not cause `pdb` to be invoked upon an exception if IGA is running as a GitHub Action.
* Documentation has been further expanded and improved.


## Version 0.0.8 (2023-05-04)

This version fixes a few minor bugs, and improves documentation.


## Version 0.0.7 (2023-04-25)

This release fixes some bugs and adds a few more features.

### What's new

* IGA now supports creating new versions of existing InvenioRDM records, via the new option `--parent-record`.

### What's changed

* Option `--read-record` has been renamed `--read-metadata` and option `--save-record` has been renamed `--save-metadata`. The goal is to make it more clear that they are about the metadata portion of an InvenioRDM record, and also to avoid possible confusion that the values they take are not record identifiers like the new `--parent-record` option.
* The short-form name of `--open` has changed from `-O` to `-o` (lower case).
* The versions of some dependencies in `requirements.txt` have been updated.


## Version 0.0.6 (2023-04-19)

This release fixes some bugs and adds a few more features.

### What's new
* CodeMeta's `downloadUrl` and `installUrl` as well as CITATION.cff's `repository-artifact` fields are now supported.
* A new repository branch `develop` is where new development now takes place on GitHub. Previously, the lazy repository maintainer didn't create a branch and instead worked out of `main`.

### What's changed

* Fix issue #3: IGA would previously incorrectly always get the latest version of files like `codemeta.json` from the repo, even if the release requested was not the latest release.
* Fix issue #4: improve name splitting algorithm to handle a situation where it failed to produce a result before.
* The list of programming languages associated with the GitHub repo is only added to the `subjects` field of the metadata record if IGA is invoked with the `--all-metadata` option. This is to make the behavior more consistent with the conditions under which other metadata fields get values from the GitHub repo.
* The name splitting algorithm has been further enhanced to handle more test cases.
* Internally, some data loading steps are much faster.


## Version 0.0.5 (2023-04-10)

This release improves IGA's detection of ROR identifiers if provided for people's affiliations in `codemeta.json` files, and checks more carefully for duplicate identifiers in the "identifiers" section of the InvenioRDM metadata record.


## Version 0.0.4 (2023-04-07)

This release works around the problem that PyPI rejects packages that have `requirements.txt` containing direct references to packages outside of PyPI. Two of our dependencies are directly affected by this:
* It prevents us from having our `requirements.txt` install our [patched version of `pybtex-apa7-style`](https://github.com/caltechlibrary/pybtex-apa7-style) unless we also release that package on PyPI. Doing so is undesirable, so we have to vendor the package within IGA's codebase. (A detailed explanation of the problem can be found in the [README file in `iga/vendor`](./iga/vendor/README.md).
* SpaCy models are only available from spaCy's GitHub repository and not as packages installable using `pip`. Since we can't have them as direct references in our `requirements.txt` file, IGA has to download spaCy models it needs at run-time the first time it needs them. The change to IGA means that we take a huge (but thankfully one-time) performance hit the first time spaCy is needed, but at least it'll happen only once and not again on subsequent runs of IGA.

Other changes in this release:
* Update the versions of some dependencies in `requirements.txt`.
* Improve trapping and reporting of internal errors during network calls.


## Version 0.0.3 (2023-04-06)

This release fixes a problem with the syntax of `setup.py` that prevented installations via `pip install git+https://github.com/caltechlibrary/iga.git`.


## Version 0.0.2 (2023-04-06)

Fixes:
* Fix issue #1: error if `--mode` option is not given.
* Fix missing dependencies in `requirements-dev.txt`.
* Fix parsing of https dependencies in `setup.py`.
* Fix bug in `requirements.txt` that caused loading the wrong copy of `pybtex-apa7-style`.
* Fix missing spaCy requirements in `requirements.txt`.
* Fix name tagging algorithm to account for changes in spaCy behavior in latest Transformer models.
* Fix tests that had gotten out of sync with the codebase.

Changes:
* (Hopefully) improve colors and readability of help text printed with `--help`.
* More documentation (still a work in progress).


## Version 0.0.1 (2023-03-31)

Alpha release created on PyPI. Fully functional but still needs testing, documentation, and addition of GitHub Action.


## Version 0.0.0 (2022-12-08)

Project repository created at https://github.com/caltechlibrary/iga
by Mike Hucka.
