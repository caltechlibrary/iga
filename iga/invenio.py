'''
invenio.py: Code for interacting with InvenioRDM

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2022 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

from   commonpy.network_utils import net
from   commonpy.data_utils import pluralized
from   dataclasses import dataclass
from   functools import partial
import json
from   sidetrack import log
import os
from   os import path

from iga.exceptions import InvenioRDMError, InternalError


# Exported data structures.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@dataclass
class InvenioRecord():
    '''Represents the record created in InvenioRDM.

    Used internally in IGA to make certain values directly accessible and to
    make it easy to pass a record around between functions. This is not exactly
    what InvenioRDM returns, but it contains values returned by InvenioRDM.
    '''
    data        : dict                  # The complete record returned by RDM.
    draft_url   : str                   # links 'self'
    record_url  : str                   # links 'record_html' URL
    publish_url : str                   # links 'publish'
    files_url   : str                   # links 'files'
    assets      : list                  # List of file names or URLs


# Exported module functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def invenio_create(metadata):
    '''Use the given metadata to create a record in the InvenioRDM server.'''
    log('sending metadata record to InvenioRDM server')
    if os.environ.get('IGA_RUN_MODE') == 'debug':
        log(json.dumps(metadata, indent=2))

    result, error = _invenio('post', endpoint='/api/records', data=metadata)
    if error:
        raise InvenioRDMError(f'Failed to create record in InvenioRDM: {error}')
    if os.environ.get('IGA_RUN_MODE') == 'debug':
        log(f'got response from {os.environ.get("INVENIO_SERVER")}:')
        log(json.dumps(result, indent=2))
    if validation_errors := result.get('errors', []):
        log(f'the server reported {pluralized("error", validation_errors, True)}:')
        for error in validation_errors:
            log(f' * in field "{error["field"]}": {error["messages"]}')
        # FIXME need to report to user
    else:
        log('record created successfully with no errors')

    record = InvenioRecord(data=result,
                           draft_url=result['links']['self'],
                           record_url=result['links']['record_html'],
                           publish_url=result['links']['publish'],
                           files_url=result['links']['files'],
                           assets=[])
    log(f'new record record_html = {record}')
    return record


def invenio_upload(record, asset):
    # Assets can be in 2 forms: a URL (to a github location) or a local file.
    # Read them 1st so we are sure we have the content before trying to upload.
    if asset.startswith('http'):
        # GH tarball & zipball URLs end in the tag name, not a meaningful name.
        parts = asset.split('/')
        if 'zipball' in asset:
            filename = f'{parts[-3]}_{parts[-1]}.zip'
        elif 'tarball' in asset:
            filename = f'{parts[-3]}_{parts[-1]}.tar.gz'
        else:
            filename = parts[-1]
        log(f'downloading {asset} ...')
        response, error = net('get', asset)
        log(f'downloading {asset} ... done.')
        if not error:
            content = response.content
    else:
        filename = asset
        content = None
        log(f'reading file {filename} ...')
        with open(asset, 'rb') as file:
            content = file.read()
        log(f'reading file {filename} ... done.')

    # Create a file upload link.
    log(f'asking InvenioRDM for a file upload link for {filename}')
    file_key = [{'key': filename}]
    response, error = _invenio('post', url=record.files_url, data=file_key)
    if error:
        log(f'failed to get upload link for {filename}')
        raise error

    for entry in response['entries']:
        if entry['key'] == filename:
            content_url = entry['links']['content']
            commit_url = entry['links']['commit']
            break
    else:
        log(f'response does not contain an entry for {filename} -- bailing')
        raise InternalError('Data mismatch in result from InvenioRDM')

    log(f'uploading content of {filename} to InvenioRDM server')
    result, error = _invenio('put', url=content_url, data=content)
    if error:
        log(f'failed to upload content of {filename}')
        raise error

    log(f'committing {filename}')
    result, error = _invenio('post', url=commit_url)
    if error:
        log(f'failed to commit {filename}')
        raise error


def invenio_publish(record, community):
    log('asking InvenioRDM server to publish the record')
    response, error = _invenio('post', url=record.publish_url)
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
    result, error = _invenio('get', endpoint=endpoint)
    if error:
        return []
    if hits := result.get('hits', {}):
        # This is not a mistake; it really is a nested 'hits' dictionary.
        num_items = len(hits['hits'])
        log(f'received {num_items} items for vocabulary "{vocab_name}"')
        if num_items < hits['total']:
            log(f'warning: server actually has {hits["total"]} values available')
        return hits['hits']
    log(f'got 0 items for vocabulary "{vocab_name}"')
    return []


def invenio_communities():
    pass


# Miscellaneous helper functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def _invenio(action, endpoint='', url='', data=None):
    '''Do HTTP action on the given endpoint with the given data & return json.'''
    assert endpoint or url, 'must provide a value for either endpoint or url'
    if endpoint:
        url = os.environ.get('INVENIO_SERVER') + endpoint
    data_type = 'json' if isinstance(data, (dict, list)) else 'octet-stream'
    headers = {'Accept': 'application/json',
               "Content-type": 'application/' + data_type,
               'Authorization': 'Bearer ' + os.environ.get('INVENIO_TOKEN')}
    api_call = partial(net, action, url, headers=headers)
    if data_type == 'json':
        data = json.dumps(data)
    response, error = api_call(data=data) if action == 'post' else api_call()
    if error:
        import commonpy.exceptions
        if isinstance(error, commonpy.exceptions.NoContent):
            # The requested thing does not exist.
            log(f'got no content for {endpoint}')
        return {}, error
    elif getattr(response, 'json'):
        return response.json(), None
    else:
        return response, None
