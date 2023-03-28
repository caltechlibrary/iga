'''
id_utils.py: utilities for dealing with identifiers

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2023 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

from idutils import (
    detect_identifier_schemes,
    is_pmid,
    normalize_arxiv,
    normalize_doi,
    normalize_gnd,
    normalize_handle,
    normalize_isbn,
    normalize_issn,
    normalize_orcid,
    normalize_pmid,
    normalize_ror,
    normalize_urn,
)
import re


# The idutils regular expression for PMCID doesn't have a capturing expression
# and also, idutils lacks a "normalize_X()" for pmcid, for some reason.
PMCID_REGEX = re.compile(r"(PMC\d{6,8})", flags=re.IGNORECASE)


def contains_pmcid(val):
    '''Return True if the given value contains a PMCID.'''
    return bool(PMCID_REGEX.match(val)) if val else False


def normalize_pmcid(val):
    '''Normalize a PubMed ID.'''
    if not val:
        return ''
    m = PMCID_REGEX.match(val.upper())
    return m.group(1) if m else ''


def normalize_isni(val):
    '''Normalize an International Standard Name Identifier (ISNI).'''
    # FIXME not sure if anything needs to be done
    return val


def normalize_swh(val):
    '''Normalize a Software Heritage identifier (SWHID).'''
    # FIXME not sure if anything needs to be done
    return val


def normalize_ark(val):
    '''Normalize an ARK identifier.'''
    return val


def normalize_ean13(val):
    '''Normalize an EAN13 identifier.'''
    return val


def normalize_istc(val):
    '''Normalize an ISTC identifier.'''
    return val


def normalize_lsid(val):
    '''Normalize an LSID identifier.'''
    return val


def normalize_purl(val):
    '''Normalize a PURL identifier.'''
    return val


def normalize_url(val):
    '''Normalize a URL.'''
    return val


RECOGNIZED_SCHEMES = {
    'ark'    : normalize_ark,
    'arxiv'  : normalize_arxiv,
    'doi'    : normalize_doi,
    'ean13'  : normalize_ean13,
    'gnd'    : normalize_gnd,
    'handle' : normalize_handle,
    'isbn'   : normalize_isbn,
    'isni'   : normalize_isni,
    'issn'   : normalize_issn,
    'istc'   : normalize_istc,
    'lsid'   : normalize_lsid,
    'orcid'  : normalize_orcid,
    'pmcid'  : normalize_pmcid,
    'pmid'   : normalize_pmid,
    'purl'   : normalize_purl,
    'ror'    : normalize_ror,
    'swh'    : normalize_swh,
    'url'    : normalize_url,
    'urn'    : normalize_urn,
}


def detected_id(text):
    '''Return a tuple (identifier, scheme) for an id found in text.'''
    if isinstance(text, str) and (scheme := recognized_scheme(text)):
        return RECOGNIZED_SCHEMES[scheme](text)
    return ''


def recognized_scheme(text):
    for scheme in detect_identifier_schemes(text):
        if scheme in RECOGNIZED_SCHEMES:
            return scheme
    else:
        # Special case not handled well by idutils. PMID's are a particular
        # PITA b/c they're integers & cause false-positives for other things.
        if contains_pmcid(text):
            return 'pmcid'
        elif is_pmid(text):
            return 'pmid'
    return None
