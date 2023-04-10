'''
doi.py: module for fetching information using DOIs

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2023 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

import commonpy.exceptions
from   commonpy.network_utils import network
from   contextlib import suppress
import functools
import json
import os
from   sidetrack import log

from   iga.id_utils import recognized_scheme
from   iga.exceptions import InternalError


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
    log(f'looking up DOI for {scheme} {pub_id} using NCBI idconv')
    url = f'https://www.ncbi.nlm.nih.gov/pmc/utils/idconv/v1.0/?format=json&ids={pub_id}'
    try:
        data = network('get', url).json()
        if os.environ.get('IGA_RUN_MODE') == 'debug':
            log(f'data received for {scheme} "{pub_id}" from NCBI:\n{str(data)}')
        with suppress(KeyError, IndexError):
            if doi := data['records'][0].get('doi'):
                return doi
            elif errmsg := data['records'][0].get('errmsg'):
                log(f'NCBI returned an error for {pub_id}: ' + errmsg)
            else:
                log(f'did not get a DOI or error message for {pub_id} from NCBI')
    except KeyboardInterrupt:
        raise
    except commonpy.exceptions.NoContent:
        log(f'NBCI returned no result for "{pub_id}"')
    except commonpy.exceptions.CommonPyException as ex:
        log(f'could not get DOI from NCBI for "{pub_id}": ' + str(ex))
    except json.JSONDecodeError as ex:
        # This means we have to fix something.
        raise InternalError('Error trying to decode JSON from NCBI: ' + str(ex))
    except Exception:
        raise
    return ''
