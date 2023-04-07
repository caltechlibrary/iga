# Change log for iga

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
