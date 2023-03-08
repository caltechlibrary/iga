'''
invenio.py: Code for interacting with InvenioRDM

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2022 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

from   commonpy.network_utils import net
from   functools import partial
import json
from   sidetrack import log
import os


# Exported module functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def invenio_write(record):
    '''Write the record to the server named in variable INVENIO_SERVER.'''
    log('writing metadata record to InvenioRDM server')
    if os.environ.get('IGA_RUN_MODE', 'normal') == 'debug':
        log(json.dumps(record, indent=2))

    response = _invenio('post', '/api/records', record)
    breakpoint()


def invenio_vocabulary(vocab_name):
    '''Return a controlled vocabulary from this server.

    The value of vocab_name must be one of "languages", "licenses", or
    "resourcetypes". This uses the API endpoint described in
    https://inveniordm.docs.cern.ch/reference/rest_api_vocabularies/.
    '''
    log(f'asking InvenioRDM server for vocabulary "{vocab_name}"')
    # At the time of this writing (2023-03-08), the "languages" vocabulary has
    # 7847 entries. We currently don't use the languages vocab in IGA, but in
    # case we ever do in the future, this code tries to get everything at once.
    endpoint = '/api/vocabularies/' + vocab_name + '?size=10000'
    json_dict = _invenio('get', endpoint)
    if hits := json_dict.get('hits', {}):
        # This is not a mistake; it really is a nested 'hits' dictionary.
        num_items = len(hits['hits'])
        log(f'received {num_items} items for vocabulary "{vocab_name}"')
        if num_items < hits['total']:
            log(f'warning: server actually has {hits["total"]} values available')
        return hits['hits']
    log(f'got 0 items for vocabulary "{vocab_name}"')
    return []


# Miscellaneous helper functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def _invenio(action, endpoint, json_dict={}):
    '''Do HTTP action on the given endpoint with the given data & return json.'''
    url = os.environ.get('INVENIO_SERVER') + endpoint
    headers = {'Accept': 'application/json',
               'Content-type': 'application/json',
               'Authorization': 'Bearer ' + os.environ.get('INVENIO_TOKEN')}
    api_call = partial(net, action, url, headers=headers)
    data = json.dumps(json_dict) if json_dict else ''
    response, error = api_call(data=data) if action == 'post' else api_call()
    if error:
        import commonpy.exceptions
        if isinstance(error, commonpy.exceptions.NoContent):
            # The requested thing does not exist.
            log(f'got no content for {endpoint}')
            return {}
        else:
            breakpoint()
    return response.json()
