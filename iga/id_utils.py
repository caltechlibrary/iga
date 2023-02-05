'''
id_utils.py: utilities for dealing with identifiers

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2023 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

from idutils import (
    detect_identifier_schemes,
    normalize_doi,
    normalize_arxiv,
    normalize_pmid,
    normalize_isbn,
    normalize_ror,
    normalize_orcid,
)
import re


# The idutils regular expression for PMCID doesn't have a capturing expression
# and also, idutils lacks a normalize_X for pmcid, for some reason.
PMCID_REGEX = re.compile(r"(PMC\d{6,8})")


def contains_pmcid(val):
    '''Return True if the given value contains a PMCID.'''
    return PMCID_REGEX.match(val)


def normalize_pmcid(val):
    '''Normalize a PubMed ID.'''
    m = PMCID_REGEX.match(val)
    return m.group(2)


RECOGNIZED_SCHEMES = {
    'arxiv': normalize_arxiv,
    'doi'  : normalize_doi,
    'isbn' : normalize_isbn,
    'orcid': normalize_orcid,
    'pmcid': normalize_pmcid,
    'pmid' : normalize_pmid,
    'ror'  : normalize_ror,
}


def detected_id(text):
    '''Return a tuple (identifier, scheme) for an id found in text.'''
    if scheme := recognized_scheme(text):
        return RECOGNIZED_SCHEMES[scheme](text)
    return ''


def recognized_scheme(text):
    for scheme in detect_identifier_schemes(text):
        if scheme in RECOGNIZED_SCHEMES:
            return scheme
    else:
        # Special case not handled well by idutils.
        if contains_pmcid(text):
            return 'pmcid'
    return None
