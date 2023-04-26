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


# We define our own type 'rdm' to pull out InvenioRDM identifiers from strings
# and URLs, and treat them all the same was as other identifiers. The id's are
# Douglas Crockford base 32 (https://github.com/inveniosoftware/base32-lib),
# which means 0-9 and letters except for i, l, o, and u.

rdm_regex = re.compile(r'([abcdefghjkmnpqrstvwxyz0-9]{5}-[abcdefghjkmnpqrstvwxyz0-9]{5})')
'''Matches an InvenioRDM record id.'''


def is_invenio_rdm(val):
    '''Return True if the given string is an InvenioRDM record identifier.'''
    return bool(normalize_invenio_rdm(val))


def normalize_invenio_rdm(val):
    '''Normalize an InvenioRDM record identifier.

    This accepts a URL that contains an InvenioRDM record identifier if the
    URL has one of the following forms:

       https://servername.domain/records/xxxxx-xxxxx
       https://servername.domain/uploads/xxxxx-xxxxx

    If the value is not actually an InvenioRDM identifier or a URL for a
    record containing the record identifier, this will return an empty string.
    '''
    candidate = val
    if val.startswith('http'):
        val = val.split('?')[0]         # Remove stuff like &preview=1.
        val = val.removesuffix('/draft')
        url_parts = val.split('/')
        if len(url_parts) < 2 or url_parts[-2] not in ['records', 'uploads']:
            return ''
        candidate = url_parts[-1]
    m = rdm_regex.match(candidate)
    return m.group(1) if m else ''


# The idutils regular expression for PMCID doesn't have a capturing expression
# and also, idutils lacks a "normalize_X()" for pmcid, for some reason.
PMCID_REGEX = re.compile(r"(PMC\d{6,8})", flags=re.IGNORECASE)


def contains_pmcid(val):
    '''Return True if the given value contains a PMCID.'''
    return bool(PMCID_REGEX.match(val)) if val else False


def normalize_pmcid(val):
    '''Normalize a PubMed ID.

    If the given value is not a PubMed ID, this returns an empty string.
    '''
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
    'rdm'    : normalize_invenio_rdm,
    'ror'    : normalize_ror,
    'swh'    : normalize_swh,
    'urn'    : normalize_urn,
    'url'    : normalize_url,
}


def detected_id(text):
    '''Return a tuple (identifier, scheme) for an id found in text.'''
    if isinstance(text, str) and (scheme := recognized_scheme(text)):
        return RECOGNIZED_SCHEMES[scheme](text)
    return ''


def recognized_scheme(text):
    # We allow URLs that contain InvenioRDM identifiers. They're URLs & would
    # be reported as 'url' by detect_identifier_schemes, so test this case 1st.
    if is_invenio_rdm(text):
        return 'rdm'
    for scheme in detect_identifier_schemes(text):
        if scheme in RECOGNIZED_SCHEMES:
            return scheme
    else:
        # Special case not handled well by idutils. PMID's are a particular
        # PITA b/c they're integers & cause false-positives for other things.
        if is_pmid(text):
            return 'pmid'
    return None
