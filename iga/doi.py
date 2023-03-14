'''
doi.py: module for fetching information using DOIs

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2023 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

from   commonpy.network_utils import net
import functools
from   sidetrack import log

from iga.id_utils import recognized_scheme


# Exported module functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def doi_for_publication(pub_id, scheme=None):
    '''Given a publication id, try to get a corresponding DOI.'''
    if not pub_id:
        return ''
    scheme = recognized_scheme(pub_id) if not scheme else scheme
    if scheme == 'doi':
        return pub_id
    elif scheme == 'arxiv':
        # As of this time, not all publications in arXiv have DOIs yet, but
        # hopefully they will eventually, so we return this for all cases:
        doi = '10.48550/' + pub_id.replace(':', '.')
        log(f'converting {pub_id} into DOI {doi}')
        return doi
    elif scheme in ['pmcid', 'pmid']:
        doi = _doi_for_pubmed(pub_id, scheme)
        log(f'looked up {pub_id} and found "{doi}" as the DOI')
        return doi
    else:
        log(f'unable to get a DOI for unsupported scheme {scheme}: ' + pub_id)
    return ''


@functools.cache
def _doi_for_pubmed(pub_id, scheme):
    '''Return a DOI for a PMCID or PMID by contacting PubMed.'''
    if not pub_id:
        return ''
    log(f'looking up DOI for {pub_id} using NCBI idconv')
    base = 'https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?format=json'
    response, error = net('get', base + '&ids=' + pub_id)
    if not error:
        try:
            data = response.json()
            if records := data.get('records', []):
                if doi := records[0].get('doi', ''):
                    log(f'got DOI {doi} for {pub_id}')
                    return doi
                elif errmsg := records[0].get('errmsg', ''):
                    log(f'NCBI returned an error for {pub_id}: ' + errmsg)
                    return ''
        except (TypeError, ValueError) as ex:
            log(f'unable to parse data from NCBI for {pub_id}: ' + str(ex))
    else:
        log(f'error trying to get DOI for {pub_id}: ' + str(error))
    return ''
