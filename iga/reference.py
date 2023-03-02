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


# Internal variables for this module.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

_CACHE = {}
'''Internal cache used to store results of some operations across calls.'''


# Exported module functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def reference(pub_id):
    '''Given an id (e.g., a DOI), return a formatted APA-style reference.'''
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
            log(f'could not find data for ISBN {pub_id}')
    else:
        # For everything other than ISBN, convert whatever ID we have to a
        # DOI, then use Crossref to get a reference as text in APA format.
        if doi := doi_for_publication(pub_id, scheme):
            formatted_reference = reference_from_doi(doi)
        else:
            log(f'could not get a DOI for {pub_id}')
    log(f'returning formatted result for {pub_id}: ' + formatted_reference)
    return formatted_reference


def reference_from_doi(doi):
    '''Given a DOI, return an APA-style formatted reference.

    This function takes advantage of Crossref's network service for generating
    reference strings in APA format. It cleans the result of HTML tags.
    '''
    global _CACHE
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
        from iga.data_utils import without_html
        log('received response from Crossref: ' + response.text)
        cleaned_text = without_html(response.text)
        _CACHE[cache_key] = cleaned_text
        return cleaned_text
    else:
        # Crossref's free API doesn't have a login but does impose rate limits.
        # More about the limits: https://api.crossref.org/swagger-ui/index.html
        # net(..) handles rate limits automatically, so this is something else.
        log('failed to get metadata from Crossref: ' + error)
        return ''


def reference_from_bibtex(bibtex_string):
    '''Give a string containing a BibTeX entry, return an APA-style reference.'''
    from pybtex.plugin import find_plugin
    from pybtex.database import parse_string
    import latexcodec                   # noqa F401

    # Cache the results of these plugin lookups for greater efficiency.
    global _CACHE
    if 'apa_style' in _CACHE:
        apa_style = _CACHE['apa_style']
        plain_text = _CACHE['plain_text']
    else:
        log('loading pybtex plugins')

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


def doi_for_publication(pub_id, scheme=None):
    '''Given a publication id, try to get a corresponding DOI.'''
    scheme = recognized_scheme(pub_id) if not scheme else scheme
    if scheme == 'doi':
        return pub_id
    elif scheme == 'arxiv':
        # As of this time, not all publications in arXiv have DOIs, but I
        # believe they're being back-filled, so hopefully, eventually all will.
        doi = '10.48550/' + pub_id.replace(':', '.')
        log(f'converting {pub_id} into DOI {doi}')
        return doi
    elif scheme in ['pmcid', 'pmid']:
        return doi_from_pubmed(pub_id, scheme)
    else:
        log(f'DOI requested for unsupported scheme ({scheme}): ' + pub_id)
    return ''


def doi_from_pubmed(pub_id, scheme):
    '''Return a DOI for a PMCID or PMID by contacting PubMed.'''
    global _CACHE
    if pub_id in _CACHE:
        cached = _CACHE[pub_id]
        log(f'returning cached DOI for {pub_id}: ' + cached)
        return cached

    import json
    log(f'looking up DOI for {pub_id} using NCBI idconv')
    base = 'https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?format=json'
    (response, error) = net('get', base + '&ids=' + pub_id)
    if not error:
        try:
            data = json.loads(response.text)
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
            log(f'unable to parse data from NCBI for {pub_id}: ' + str(ex))
            return ''
    else:
        log(f'error trying to get DOI for {pub_id}: ' + str(error))
        return ''
