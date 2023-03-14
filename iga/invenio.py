'''
invenio.py: Code for interacting with InvenioRDM

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2022 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

from   commonpy.network_utils import net, netloc
from   commonpy.data_utils import pluralized
from   dataclasses import dataclass
from   functools import partial, cache
import json
from   sidetrack import log
import socket
import os
from   os import path

from iga.exceptions import InvenioRDMError, InternalError


# Exported data structures.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@dataclass
class InvenioRecord():
    '''Represents the record created in InvenioRDM.

    Used internally in IGA to make certain values directly accessible and to
    make it easy to pass a record around between functions. This is not what
    InvenioRDM returns directly, but it contains values returned by InvenioRDM.
    '''
    data        : dict                  # The complete record returned by RDM.
    draft_url   : str                   # links 'self'
    record_url  : str                   # links 'record_html' URL
    publish_url : str                   # links 'publish'
    files_url   : str                   # links 'files'
    assets      : list                  # List of file names or URLs


@dataclass
class InvenioCommunity():
    '''Represents information about an Invenio community in InvenioRDM.'''
    data  : dict                       # The complete record returned by RDM.
    name  : str                        # The slug field value
    url   : str                        # The links['self_html'] field value
    id    : str                        # The id field value
    title : str                        # The metadata['title'] value


# Exported module functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def invenio_api_available():
    '''Return True if the INVENIO_SERVER responds to API calls.'''
    server_url = os.environ.get('INVENIO_SERVER')
    server_host = netloc(server_url)
    test_endpoint = '/api/records?size=1'
    try:
        log(f'testing if we can reach {server_url} in 5 sec or less')
        socket.setdefaulttimeout(5)
        # If this can't reach the host, it'll throw an exception.
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((server_host, 443))
        # If we can reach the host, now check that the API endpoint works.
        response, error = net('get', server_url + test_endpoint)
        if not error:
            log(f'yes, we can reach {server_url} and its API endpoint')
            return True
        else:
            log(f'{server_url} is reachable but it doesn\'t respond to /api/records')
    except KeyboardInterrupt as ex:
        raise ex
    except Exception as ex:
        log(f'failed to reach server {server_url}: {str(ex)}')
    return False


def invenio_create(metadata):
    '''Create a record in the InvenioRDM server using the given metadata.

    This only creates a record, and returns an InvenioRecord data class; it
    does not upload file attachments, which is something handled by a separate
    function, invenio_upload(...).
    '''
    log('sending metadata to InvenioRDM server')
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

    breakpoint()
    record = InvenioRecord(data=result,
                           draft_url=result['links']['self_html'],
                           record_url=result['links']['record_html'],
                           publish_url=result['links']['publish'],
                           files_url=result['links']['files'],
                           assets=[])
    log(f'new record record_html = {record.record_url}')
    return record


def invenio_upload(record, asset):
    '''Upload a file asset to InvenioRDM and attach it to the record.

    Assets can be in one of 2 forms: a URL (a github location) or a local file.
    This will read the file into memory, then send it to the InvenioRDM server
    and commit the upload.
    '''
    # Start by reading the assets to be sure we can actually get them, *before*
    # trying to upload them to InvenioRDM.
    if asset.startswith('http'):
        filename = _filename_from_asset_url(asset)
        log(f'downloading {asset} ...')
        response, error = net('get', asset)
        if error:
            log(f'failed to download {asset}')
            return
        content = response.content
        log(f'downloaded {len(content)} bytes of {asset}')
    else:
        filename = path.basename(asset)
        content = None
        log(f'reading file {filename} ...')
        with open(asset, 'rb') as file:
            content = file.read()
        log(f'read {len(content)} bytes of file {filename}')

    # Define a helper function for the remaining steps.
    def action(op, url, thing, **kwargs):
        log(f'doing {op} to InvenioRDM server for {filename} {thing}')
        result, error = _invenio(op, url=url, **kwargs)
        if error:
            log(f'failed {op} for {filename} {thing}')
            raise error
        elif os.environ.get('IGA_RUN_MODE') == 'debug':
            log(f'response from server for {url}:')
            log(json.dumps(result, indent=2))
        log(f'successfully did {op} for {filename} {thing}')
        return result

    # Get a file upload link from the server, then using that, do a 'put' to
    # write the content followed with a 'post' to commit the new file.
    key = [{'key': filename}]
    result = action('post', record.files_url, 'file upload link', data=key)
    for entry in result['entries']:
        if entry['key'] == filename:
            content_url = entry['links']['content']
            commit_url = entry['links']['commit']
            break
    else:
        log(f'server data did not contain an entry for {filename} -- bailing')
        raise InternalError('Data mismatch in result from InvenioRDM')

    action('put', content_url, 'upload', data=content)
    action('post', commit_url, 'commit')


def invenio_publish(record, community):
    '''Tell the InvenioRDM server to publish the record.'''
    log('telling the server to publish the record')
    result, error = _invenio('post', url=record.publish_url)
    if error:
        raise error
    if community:
        # cli() will have checked that the given community exists.
        communities = invenio_communities()
        community_id = communities[community]


@cache
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


@cache
def invenio_communities():
    '''Return a dict of communities available in this InvenioRDM server.'''
    log('getting the list of communities from the server')
    result, error = _invenio('get', endpoint='/api/communities')
    if error:
        raise error
    communities = {}
    for community in result.get('hits', {}).get('hits', []):
        name = community['slug']
        metadata = community['metadata']
        title = metadata.get('title', '')
        access = community['access']
        if access['visibility'] != 'public':
            log(f'community {name} is not publicly visible; skipping')
            continue
        communities[name] = InvenioCommunity(data=community,
                                             name=name,
                                             url=community['links']['self_html'],
                                             id=community['id'],
                                             title=title)
    log(f'we got back {pluralized("community", communities, True)}')
    return communities


# Miscellaneous helper functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def _invenio(action, endpoint='', url='', data=''):
    '''Do HTTP action on the given endpoint with the given data & return json.

    Either (but not both) the full url, or the endpoint part, must be given as
    an argument. The data is optional, and can be a JSON dict or a binary
    string.
    '''
    if endpoint:
        url = os.environ.get('INVENIO_SERVER') + endpoint
    data_type = 'json' if isinstance(data, (dict, list)) else 'octet-stream'
    headers = {'Content-type': 'application/' + data_type}
    if token := os.environ.get('INVENIO_TOKEN'):
        headers['Authorization'] = 'Bearer ' + token

    # Construct a Python partial to gather most of the args for calling net().
    client = None
    if action == 'put':
        # 'put' => data is being uploaded, so we need to set longer timeouts.
        import httpx
        tmout = _network_timeout(data)
        timeout = httpx.Timeout(tmout, connect=10, read=tmout, write=tmout)
        client = httpx.Client(timeout=timeout, http2=True, verify=False)

    # Now perform the actual network api call.
    api_call = partial(net, action, url, client=client, headers=headers)
    if data:
        log(f'data payload size = {len(data)}')
        if data_type == 'json':
            response, error = api_call(json=data)
        else:
            response, error = api_call(content=data)
    else:
        response, error = api_call()

    # Interpret the results.
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


def _network_timeout(data):
    '''Return a timeout value (in seconds) for writing the given data string.

    This uses the value in the environment variable IGA_NETWORK_TIMEOUT, if
    given. If no explicit timeout value has been given, this calculates an
    adaptive timeout value based on the size of the data, using a custom
    heuristic invented by the author based on his experiences with a
    slowish network.
    '''
    if given_timeout := os.environ.get('IGA_NETWORK_TIMEOUT', None):
        # Assume that the main cli() has done sanity-checking on the value.
        timeout = int(given_timeout)
    else:
        # Calculate a value based on these principles:
        #  - Scale by the size of the data at roughly 1 min per 5 MB
        #  - Don't exceed 30 minutes (1800 sec)
        timeout = min(1800, 60*max(1, len(data)//2_000_000))
    log(f'using a network timeout of {timeout} s')
    return timeout


def _filename_from_asset_url(asset):
    '''Return a file name based on a GitHub asset URL.

    This function exists because GitHub tarball & zipball URLs end in the tag
    name, not a meaningful name, so we have to make up our own.
    '''
    parts = asset.split('/')
    if 'zipball' in asset:
        return f'{parts[-3]}_{parts[-1]}.zip'
    elif 'tarball' in asset:
        return f'{parts[-3]}_{parts[-1]}.tar.gz'
    else:
        return parts[-1]
