'''
reference.py: create a formatted reference for a given publication.

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2023 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

from commonpy.network_utils import net
from sidetrack import log

from iga.id_utils import recognized_scheme


# Constants for this module.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

_CACHE = {}
'''Internal cache used to store results of some operations across calls.'''


# Exported module functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def reference(pub_id):
    scheme = recognized_scheme(pub_id)
    log(f'reference {pub_id} has scheme {scheme}')

    formatted_reference = ''
    if scheme == 'isbn':
        # ISBNs cannot be converted to DOIs & have to be handled separately.
        import isbnlib
        from   isbnlib.registry import bibformatters as isbn_bibformatters
        if isbn_metadata := isbnlib.meta(pub_id):
            log(f'got metadata for ISBN {pub_id}: ' + str(isbn_metadata))
            bibtex_string = isbn_bibformatters['bibtex'](isbn_metadata)
            formatted_reference = reference_from_bibtex(bibtex_string)
        else:
            # Sometimes ISBN can't be found. Not clear what can be done here.
            log('could not find data for ISBN ' + pub_id)
    else:
        # For everything other than ISBN, convert whatever ID we have to a
        # DOI, then use Crossref to get a reference as text in APA format.
        doi = doi_for_publication(pub_id, scheme)
        formatted_reference = reference_from_doi(doi)
    log(f'returning formatted result for {pub_id}: ' + formatted_reference)
    return formatted_reference


def reference_from_doi(doi):
    cache_key = doi + '-reference'
    if cache_key in _CACHE:
        cached = _CACHE[cache_key]
        log(f'returning cached reference for {doi}: ' + cached)
        return cached

    log(f'asking Crossref for metadata about {doi}')
    doi_url = 'https://doi.org/' + doi
    headers = {'accept': 'text/x-bibliography; style=apa'}
    (response, error) = net('get', doi_url, headers=headers)
    if not error:
        log('received response from Crossref: ' + response.text)
        cleaned_text = clean_text(response.text)
        _CACHE[cache_key] = cleaned_text
        return cleaned_text
    else:
        # Crossref's free API doesn't have a login but does impose rate limits.
        # More about the limits: https://api.crossref.org/swagger-ui/index.html
        # net(..) handles rate limits automatically, so this is something else.
        log('failed to get metadata from Crossref: ' + error)
        return ''


def reference_from_bibtex(bibtex_string):
    # Cache the results of these plugin lookups for greater efficiency.
    if 'apa_style' in _CACHE:
        apa_style = _CACHE['apa_style']
        plain_text = _CACHE['plain_text']
    else:
        from pybtex.plugin import find_plugin
        from pybtex.database import parse_string

        # This requires pip install pybtex-apa7-style.
        apa_style = find_plugin('pybtex.style.formatting', 'apa7')()
        plain_text = find_plugin('pybtex.backends', 'text')()
        _CACHE['apa_style'] = apa_style
        _CACHE['plain_text'] = plain_text

    bib_data = parse_string(bibtex_string, 'bibtex')
    formatted_bib = apa_style.format_bibliography(bib_data)

    # formatted_bib is an iterable object, but not an iterator. We know there's
    # only one, so just do a next() after creating an iterator out of it.
    formatted_item = next(iter(formatted_bib))
    return formatted_item.text.render(plain_text)


def doi_for_publication(pub_id, scheme = None):
    scheme = recognized_scheme(pub_id) if not scheme else scheme
    if scheme == 'doi':
        return pub_id
    elif scheme == 'arxiv':
        return '10.48550/' + pub_id.replace(':', '.')
    elif scheme in ['pmcid', 'pmid']:
        return doi_from_pubmed(pub_id, scheme)
    else:
        log(f'DOI requested for unsupported scheme ({scheme}): ' + pub_id)


def doi_from_pubmed(pub_id, scheme):
    if pub_id in _CACHE:
        cached = _CACHE[pub_id]
        log(f'returning cached DOI for {pub_id}: ' + cached)
        return cached

    import json5
    log(f'looking up DOI for {pub_id} using NCBI idconv')
    base = 'https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?format=json'
    (response, error) = net('get', base + '&ids=' + pub_id)
    if not error:
        try:
            data = json5.loads(response.text)
            if records := data.get('records', []):
                if doi := records[0].get('doi', ''):
                    log(f'got DOI {doi} for {pub_id}')
                    _CACHE[pub_id] = doi
                    return doi
                elif errmsg := records[0].get('errmsg', ''):
                    log(f'NCBI returned an error for {pub_id}: ' + errmsg)
                    _CACHE[pub_id] = ''
                    return ''
        except (TypeError, ValueError) as ex:
            log('unable to parse data from NCBI: ' + str(ex))
            return ''
    else:
        log(f'error trying to get DOI for {pub_id}: ' + str(error))
        return ''


def clean_text(text):
    from lxml import html
    try:
        return html.fromstring(text).text_content().strip()
    except Exception:                   # noqa PIE786
        return text
