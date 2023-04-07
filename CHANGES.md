# Change log for iga

## Version 0.0.4

This release works around the problem that PyPI rejects packages that have `requirements.txt` containing direct references to packages outside of PyPI. Two of our dependencies are directly affected by this:
* It prevents us from having our `requirements.txt` install our [patched version of `pybtex-apa7-style`](https://github.com/caltechlibrary/pybtex-apa7-style) unless we also release that package on PyPI. Doing so is undesirable, so we have to vendor the package within IGA's codebase. (A detailed explanation of the problem can be found in the [README file in `iga/vendor`](./iga/vendor/README.md).
* SpaCy models are only available from spaCy's GitHub repository and not as packages installable using `pip`. Since we can't have them as direct references in our `requirements.txt` file, IGA has to download spaCy models it needs at run-time the first time it needs them. The change to IGA means that we take a huge (but thankfully one-time) performance hit the first time spaCy is needed, but at least it'll happen only once and not again on subsequent runs of IGA.


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
