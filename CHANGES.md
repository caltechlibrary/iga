# Change log for IGA

## Version 1.3.5

This release adds CFF updating as part of the example workflow.

## Version 1.3.4

Bug fix release for automatic CodeMeta updating workflow. Also updates the documentation build process.

## Version 1.3.3

Bug fix release for automatic CodeMeta updating workflow

## Version 1.3.2

Bug fix release for automatic CodeMeta updating workflow

## Version 1.3.1

Changes in this release

* Adds support for automatically updating a CodeMeta.json file when used on GitHub actions
* Fixes bug https://github.com/caltechlibrary/iga/issues/39 that impacted RDM repositories with no records
* Un-pins dependencies so iga will work better with other python installs, and pins rich-click to avoid bug #40
* Switches to the v1 branch instead of master
* Simplifies release workflow

## Version 1.3.0

Changes in this release:

* Fix issue: when we have a parent id for a record,  records should not go through the community review workflow. (Fix implemented by @tmorrell.)
* Fix issue #14: try to make better guesses at person names containing CJK characters.
* Updated the IGA workflow to use the latest versions of GitHub Actions dependencies; this avoids runtime warnings about the version of Node being used by GitHub runners.
* Updated Python dependencies.
* Added a new GitHub Actions workflow for linting the Markdown files.
* Added a new GitHub Actions workflow to check URLs in Markdown files and reports invalid or broken links.
* Edited the README file to follow the Markdown lint rules and to add alt text to images.
* Minor other internal code changes have been made.
* Updated copyright year.
* Updated miscellaenous repository files to match current Library template versions of those files.


## Version 1.2.2 (2023-11-08)

Changes in this release:

* Fixed [issue #28](https://github.com/caltechlibrary/iga/issues/28): catch and report the case where a repo has no releases.
* Fixed a bug that manifested when the GitHub access token was invalid.
* Fixed a syntax bug in the Makefile.
* Improved (hopefully) the caching of python dependencies to actually work this time.
* Improved (hopefully) some of the diagnostic error messages.
* Added Tom Morrell to the CITATION.cff file.


## Version 1.2.1 (2023-07-24)

Changes in this release:

* Fixed `setup.cfg`, which had some garbled content.
* Fixed the GitHub Action for building the IGA documentation pages to avoid needlessly running it on every push.
* The GitHub Actions workflow (`action.yml`) for IGA now caches Python package dependencies for a slight speed up in run times on GitHub.
* Added a GitHub Actions workflow to lint the code on pushes & pull requests.


## Version 1.2.0 (2023-07-18)

This version fixes problems with handling Invenio Communities. First, an internal bug in IGA would cause an exception if the user attempted to list communities in an InvenioRDM server that defined more than one community. Second, a bug in InvenioRDM itself meant that community links were broken. (Thanks to @tmorrell for a fix via PR #23.)

Additional changes in this version:

* Switched to using `codemeta.json` as the main source of truth for version info. The `setup.cfg` file is now updated from `codemeta.json`, not the other way around.
* With respect to how the InvenioRDM metadata field `related_identifiers` is handled, the IGA [documentation](https://caltechlibrary.github.io/iga/appendix.html#record-metadata) and the [Google spreadsheet describing how IGA maps fields](https://docs.google.com/spreadsheets/d/1QgFrZIhip1qKA_M45QkeYe9SH238XL1K/edit?usp=sharing&ouid=111701691832013929970&rtpof=true&sd=true) both omitted the use of CodeMeta fields `downloadUrl` and `installUrl` and CFF field `repository-artifact`. These fields are now in the documentation.
* The Makefile has been updated in various ways based on experiences with other projects.


## Version 1.1.0 (2023-05-31)

New features:

* New option `--print-doi` makes IGA print the DOI of a published record in addition to printing the URL. (Without the option, IGA only prints the URL.)

Changes:

* The color of text messages printed to the terminal has been changed slightly in an effort to improve readability.
* The versions of some dependencies in `requirements.txt` have been updated.
* Documentation has been updated and expanded.


## Version 1.0.3 (2023-05-24)

Changes in this release:

* The sample workflow has been revised to be slightly more informative about where it's sending the release for archiving.


## Version 1.0.2 (2023-05-23)

Changes in this release:

* Fix issue #21: the copyright year put in the metadata `dates` field can could up being a completely bogus value in some cases.


## Version 1.0.1 (2023-05-22)

Changes in this release:

* Fix issue #8: org parsing some results in error.


## Version 1.0.0 (2023-05-18)

This is the first full release of IGA, the _InvenioRDM GitHub Archiver_. This release supports the use of IGA as both a command-line program and as a GitHub Action. Complete documentation is available at <https://caltechlibrary.github.io/iga/> and a shortened version of the documentation is present in the [repository README file](https://github.com/caltechlibrary/iga).


## Version 0.0.16 (2023-05-17)

Changes in this release:

* Fixed another problem with logging, in part by reverting a previous change but also by modifying the code that writes error messages.
* Expanded the error catches in the GitHub Action workflow to detect and report problems with invalid tokens.
* Merge PR #7: doc improvements.


## Version 0.0.15 (2023-05-17)

Changes in this version:

* IGA now tests the InvenioRDM token explicitly and returns a new exit code if the token is rejected. This makes it possible for the GitHub Action to report this situation more clearly.


## Version 0.0.14 (2023-05-16)

Changes in this release:

* Fixed bug where setting `verbose` mode or higher caused output to go to the terminal and was not properly sent to the log destination.


## Version 0.0.13 (2023-05-16)

Changes in this release:

* IGA detects the case where InvenioRDM refuses the token, and reports the error more explicitly.
* More documentation updates.
* Fixes to test cases.


## Version 0.0.12 (2023-05-12)

Changes in this release:

* A preliminary GitHub Action workflow is available.
* Documentation is more complete.


## Version 0.0.11 (2023-05-10)

Changes in this release:

* Fixed behavior of `--mode quiet`: it was not completely quiet after all, but now it is.
* Fixed behavior when `--log-dest` is used; not all output was going to the log destination, but now it is.
* Fixed additional minor issues.


## Version 0.0.10 (2023-05-09)

Changes in this release:

* IGA won't fail if the GitHub release description is empty and the repo doesn't have a `codemeta.json` nor a `CITATION.cff` file.
* IGA won't fail if the GitHub repo doesn't have a license and there are no `codemeta.json` or `CITATION.cff` files.
* IGA will properly get release assets from private repos (assuming the user has access to the private repo). Previously, it would erroneously think the repo had no assets.


## Version 0.0.9 (2023-05-08)

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

Project repository created at [https://github.com/caltechlibrary/iga](https://github.com/caltechlibrary/iga)
by Mike Hucka.
