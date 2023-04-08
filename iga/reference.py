'''
reference.py: create a formatted reference for a given publication.

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2023 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

from   commonpy.network_utils import network
import commonpy.exceptions
import json
from   sidetrack import log

from iga.doi import doi_for_publication
from iga.exceptions import InternalError
from iga.id_utils import recognized_scheme
from iga.text_utils import without_html


# Internal variables for this module.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

_CACHE = {}
'''Internal cache used to store results of some operations across calls.'''


# Exported constants.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

RECOGNIZED_REFERENCE_SCHEMES = ['arxiv', 'doi', 'isbn', 'pmcid', 'pmid']


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
    elif scheme in RECOGNIZED_REFERENCE_SCHEMES:
        # For everything other than ISBN, convert whatever ID we have to a
        # DOI, then use Crossref to get a reference as text in APA format.
        if doi := doi_for_publication(pub_id, scheme):
            formatted_reference = reference_from_doi(doi)
        else:
            log(f'could not get a DOI for {pub_id}')
    else:
        log(f'cannot convert a {scheme} type id into a formatted reference')
        return ''

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

    log(f'asking DOI.org for formatted reference for {doi}')
    doi_url = 'https://doi.org/' + doi
    headers = {'accept': 'text/x-bibliography; style=apa'}
    try:
        response = network('get', doi_url, headers=headers)
        log('received response from Crossref:\n' + response.text)
        text = without_html(response.text)
        _CACHE[cache_key] = text
        return text
    except KeyboardInterrupt:
        raise
    except commonpy.exceptions.NoContent:
        log(f'CrossRef returned no result for "{doi}"')
    except commonpy.exceptions.CommonPyException as ex:
        log(f'could not get data from CrossRef for "{doi}": ' + str(ex))
    except json.JSONDecodeError as ex:
        # This means we have to fix something.
        raise InternalError('Error trying to decode JSON from CrossRef: ' + str(ex))
    except Exception:
        raise
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

        # Currently have to use our own patched version of pybtex-apa7-style.
        # apa_style = find_plugin('pybtex.style.formatting', 'apa7')()
        from .vendor.pybtex_apa7_style.formatting.apa import APAStyle
        apa_style = APAStyle()
        plain_text = find_plugin('pybtex.backends', 'text')()
        _CACHE['apa_style'] = apa_style
        _CACHE['plain_text'] = plain_text

    bib_data = parse_string(bibtex_string, 'bibtex')
    formatted_bib = apa_style.format_bibliography(bib_data)

    # formatted_bib is an iterable object, but not an iterator. We know there's
    # only one, so just do a next() after creating an iterator out of it.
    formatted_item = next(iter(formatted_bib))
    return formatted_item.text.render(plain_text)
