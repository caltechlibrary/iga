'''
reference_utils.py: utilities for working with references

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2023 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

from commonpy.network_utils import net
from pybtex.plugin import find_plugin
from pybtex.database import parse_string
from sidetrack import log

from iga.id_utils import recognized_scheme


# Constants for this module.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# BibTeX formatting utilities.
APA_STYLE = find_plugin('pybtex.style.formatting', 'apa7')()
TEXT_RENDERER = find_plugin('pybtex.backends', 'text')()


# Exported module functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def reference(pub_id):
    scheme = recognized_scheme(pub_id)

    # ISBNs can't be converted to DOIs, so they have to be handled separately.
    # For all others, first convert whatever ID we have to a DOI, then use
    # Crossref to get a reference as text in APA format.
    if scheme == 'isbn':
        import isbnlib
        from   isbnlib.registry import bibformatters as isbn_bibformatters

        # Sometimes ISBN can't be found.
        if isbn_metadata := isbnlib.meta(pub_id):
            bibtex_string = isbn_bibformatters['bibtex'](isbn_metadata)
            return reference_from_bibtex(bibtex_string)
        else:
            log('could not find data for ISBN ' + pub_id)
            return ''
    else:
        doi = doi_for_publication(pub_id, scheme)
        return reference_from_doi(doi)


def doi_for_publication(pub_id, scheme):
    if scheme == 'doi':
        return pub_id
    elif scheme == 'arxiv':
        return 'https://doi.org/' + pub_id
    elif scheme == 'pmcid':
        # FIXME
        pass
    elif scheme == 'pmid':
        # FIXME
        pass
    else:
        log(f'DOI requested for unsupported scheme ({scheme}): ' + pub_id)


def reference_from_doi(doi):
    headers = {'accept': 'text/x-bibliography; style=apa'}
    doi_url = 'https://doi.org/' + doi
    (response, error) = net('get', doi_url, headers=headers)
    if not error:
        # Watch out that the text from doi.org often has HTML tags in it.
        return clean_text(response.text)
    else:
        import commonpy.exceptions
        if isinstance(error, commonpy.exceptions.RateLimitExceeded):
            # FIXME
            return ''
        elif isinstance(error, commonpy.exceptions.CommonPyException):
            # FIXME
            return ''


def reference_from_bibtex(bibtex_string):
    bib_data = parse_string(bibtex_string, 'bibtex')
    formatted_bib = APA_STYLE.format_bibliography(bib_data)

    # formatted_bib is an iterable object, but not an iterator. We know there's
    # only one, so just do a next() after creating an iterator out of it.
    formatted_item = next(iter(formatted_bib))
    return formatted_item.text.render(TEXT_RENDERER)


def clean_text(text):
    from lxml import html
    try:
        return html.fromstring(text).text_content().strip()
    except Exception:                   # noqa PIE786
        return text
