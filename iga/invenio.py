'''
invenio.py: Code for interacting with InvenioRDM

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2022-2023 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

from   commonpy.network_utils import net, network, netloc
from   commonpy.data_utils import pluralized
import commonpy.exceptions
from   dataclasses import dataclass
from   functools import partial, cache
import json
from   sidetrack import log
import socket
import os
from   os import path

import iga
from   iga.exceptions import (
    InternalError,
    InvenioRDMError,
    RecordNotFound,
)
from   iga.github import github_asset_contents
from   iga.id_utils import normalize_invenio_rdm


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
    review_url  : str                   # links 'review'
    publish_url : str                   # links 'publish'
    record_url  : str                   # links 'record_html' URL
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

def invenio_api_available(server_url):
    '''Return True if the server at server_url responds to the InvenioRDM API.'''
    # There is no 'status' or similarly simple API test endpoint for InvenioRDM,
    # so to test that the destination is actually an InvenioRDM server, the
    # approach here is to do some kind of minimum call that requires the API.
    return bool(invenio_server_name(server_url))


def invenio_token_valid(server_url):
    '''Return True if the token in env variable INVENIO_TOKEN is valid.'''
    # Testing things ahead of time is a Python anti-pattern, but in interactive
    # programs (and especially ones that run as GHAs) we don't want to get far
    # into the work before discovering we won't be able to upload the result.
    try:
        return bool(_invenio('get', endpoint='/api/users?size=1',
                             msg='confirm InvenioRDM token is valid'))
    except KeyboardInterrupt:
        raise
    except commonpy.exceptions.AuthenticationFailure:
        return False
    except Exception as ex:             # noqa PIE786
        log('exception while testing the InvenioRDM token: ' + str(ex))
        return False


@cache
def invenio_server_name(server_url):
    '''Return the name of server at server_url if it responds to API calls.'''
    server_host = netloc(server_url)
    endpoint = '/api/records?size=1'
    try:
        log(f'testing if we can reach {server_url} in 5 sec or less')
        socket.setdefaulttimeout(5)
        # If the next one can't reach the host, it'll throw an exception.
        socket.socket(socket.AF_INET, socket.SOCK_STREAM).connect((server_host, 443))
        # If we can reach the host, check that it responds to the API endpoint.
        if response := network('get', server_url + endpoint):
            log(f'we can reach {server_url} and it responds to {endpoint}')
            data = response.json()
            record = data.get('hits', {}).get('hits', {})[0]
            return record['metadata']['publisher']
    except KeyboardInterrupt:
        raise
    except socket.error:
        log(f'{server_url} did not respond')
        return None
    except json.decoder.JSONDecodeError:
        log(f'{server_url} exists but does not recognize the InvenioRDM API')
        return None
    except commonpy.exceptions.CommonPyException as ex:
        log(f'trying to get {server_url}{endpoint} produced an error: ' + str(ex))
        return None
    except Exception as ex:
        log(f'unexpected exception accessing {server_url}{endpoint}: ' + str(ex))
        raise
    log(f'failed to reach server {server_url}')
    return None


def invenio_get(record_id):
    '''Get the InvenioRDM record with the given identifier.'''
    log(f'asking InvenioRDM server for record {record_id}')
    record_id = normalize_invenio_rdm(record_id)
    result = _invenio('get', endpoint=f'/api/records/{record_id}',
                      msg='get record {record_id}')
    if result is None:
        # Maybe it's a draft record -- try one more time with /draft appended.
        result = _invenio('get', endpoint=f'/api/records/{record_id}/draft',
                          msg='get record {record_id}')
    if result is None:
        raise RecordNotFound(f'Could not find record with id {record_id}')
    return result


def invenio_create(metadata, parent_id=None):
    '''Create a record in the InvenioRDM server using the given metadataa.

    This only creates a draft record, and returns an InvenioRecord data class;
    it does not upload file attachments, which is something handled by a
    separate function, invenio_upload(...), or publish the record, which is
    handled by invenio_publish(...).
    '''
    # Relevant InvenioRDM documentation:
    # https://inveniordm.docs.cern.ch/reference/rest_api_drafts_records/#drafts
    # https://inveniordm.docs.cern.ch/reference/rest_api_drafts_records/#versions
    if parent_id:
        # Make sure parent actually exists. The resulting record is not needed.
        invenio_get(parent_id)

        log(f'creating a new version of record {parent_id} in InvenioRDM')
        result = _invenio('post', endpoint=f'/api/records/{parent_id}/versions',
                          msg='create new record using metadata')
        if not result:
            raise InvenioRDMError(f'Unable to create new version of {parent_id}')
        record_id = result['id']

        log(f'updating metadata in new record {record_id} in InvenioRDM')
        metadata['files'] = {'enabled': True}
        result = _invenio('put', endpoint=f'/api/records/{record_id}/draft',
                          data=metadata, msg='create new record using metadata')
        # The server will make some changes to the metadata we send.
        result['metadata'] = metadata
    else:
        log('creating record in InvenioRDM')
        result = _invenio('post', endpoint='/api/records', data=metadata,
                          msg='create new record using metadata')

    if validation_errors := result.get('errors', []):
        log(f'the server reported {pluralized("error", validation_errors, True)}:')
        for error in validation_errors:
            log(f' * in field "{error["field"]}": {error["messages"]}')
        # FIXME some should be reported to the user, but others are harmless.
    else:
        log('record created successfully with no errors')

    record = InvenioRecord(data=result,
                           draft_url=result['links']['self_html'],
                           review_url=result['links']['review'],
                           publish_url=result['links']['publish'],
                           record_url='',
                           files_url=result['links']['files'],
                           assets=[])
    log(f'new record record_html = {record.draft_url}')
    return record


def invenio_upload(record, asset, print_status):
    '''Upload a file asset to InvenioRDM and attach it to the record.

    Assets can be in one of 2 forms: a URL (a github location) or a local file.
    This will read the file into memory, then send it to the InvenioRDM server
    and commit the upload.
    '''
    # Start by reading the assets to be sure we can actually get them, *before*
    # trying to upload them to InvenioRDM.
    import humanize
    size = ''
    if asset.startswith('http'):
        filename = _filename_from_asset_url(asset)
        print_status(f' - Downloading [bold]{filename}[/] from GitHub', end='...')
        content = github_asset_contents(asset)
        print_status('done')
        size = humanize.naturalsize(len(content))
        log(f'downloaded {size} bytes of {asset}')
    else:
        filename = path.basename(asset)
        content = None
        print_status(f' - Reading [bold]{filename}[/]', end='...')
        with open(asset, 'rb') as file:
            content = file.read()
        print_status('done')
        size = humanize.naturalsize(len(content))
        log(f'read {size} bytes of file {filename}')

    # Define a helper function for the remaining steps.
    def action(op, url, dothing, **kwargs):
        log(f'doing {op} to InvenioRDM server to {dothing} {filename}')
        result = _invenio(op, url=url, msg=f'{dothing} {filename}', **kwargs)
        log(f'successfully did {op} to {dothing} {filename}')
        return result

    # Get a file upload link from the server, then using that, do a 'put' to
    # write the content followed with a 'post' to commit the new file.
    key = [{'key': filename}]
    print_status(f' - Sending [bold]{filename}[/] ({size}) to InvenioRDM', end='...')
    result = action('post', record.files_url, 'initialize upload of file', data=key)
    for entry in result.get('entries', []):
        if entry['key'] == filename:
            content_url = entry['links']['content']
            commit_url = entry['links']['commit']
            break
    else:
        log(f'server data did not contain an entry for {filename} – bailing')
        raise InternalError('Data mismatch in result from InvenioRDM')

    action('put', content_url, 'upload', data=content)
    action('post', commit_url, 'commit')
    print_status('done')


def invenio_community_send(record, community):
    '''Send the record to the InvenioRDM community for review.'''
    # cli() checks the given community exists so we don't need to do it here.
    communities = invenio_communities()
    community_id = communities[community].id

    log(f'getting the submission link for community {community} ({community_id})')
    data = {
        "receiver": {"community": community_id},
        "type": "community-submission",
    }
    result = _invenio('put', url=record.review_url, data=data,
                      msg='get community submission link from InvenioRDM')
    if submit_url := result.get('links', {}).get('actions', {}).get('submit', ''):
        data = {
            'payload': {
                'format': 'html',
                'content': 'This record is being submitted automatically using'
                f'the InvenioRDM GitHub Archiver (IGA) version {iga.__version__}',
            }
        }
        log(f'submitting the record to community {community}')
        result = _invenio('post', url=submit_url, data=data,
                          msg='submit record to community {community}')
    else:
        raise InternalError('Unexpected result in community submission step')


def invenio_publish(record):
    '''Tell the InvenioRDM server to publish the record.'''
    log('telling the server to publish the record')
    result = _invenio('post', url=record.publish_url, msg='publish record')
    record.record_url = result.get('links', {}).get('self_html', '')
    log(f'successfully published record at {record.record_url}')


@cache
def invenio_vocabulary(vocab):
    '''Return a controlled vocabulary from this server.

    The value of vocab must be one of "languages", "licenses", or
    "resourcetypes". This uses the API endpoint described in
    https://inveniordm.docs.cern.ch/reference/rest_api_vocabularies/.
    '''
    log(f'asking InvenioRDM server for vocabulary "{vocab}"')
    # At the time of this writing (2023-03-08), the "languages" vocabulary has
    # 7847 entries. We currently don't use the languages vocab in IGA, but in
    # case we ever do in the future, this code tries to get everything at once.
    endpoint = '/api/vocabularies/' + vocab + '?size=10000'
    result = _invenio('get', endpoint=endpoint, msg=f'get vocabulary {vocab}')
    if hits := result.get('hits'):
        # This is not a mistake; it really is a nested 'hits' dictionary.
        num_items = len(hits['hits'])
        log(f'received {num_items} items for vocabulary "{vocab}"')
        if num_items < hits['total']:
            log(f'warning: server actually has {hits["total"]} values available')
        return hits['hits']
    else:
        log(f'failed to get any items for vocabulary "{vocab}"')
    return []


@cache
def invenio_communities():
    '''Return a dict of communities available in this InvenioRDM server.'''
    log('asking InvenioRDM server for a list of communities')
    communities = {}
    result = _invenio('get', endpoint='/api/communities', msg='get communities list')
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
    log(f'we got {pluralized("community", communities, True)}')
    return communities


# Miscellaneous helper functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def _invenio(action, endpoint='', url='', data='', msg=''):
    '''Do HTTP action on the given endpoint with the given data & return json.

    Either (but not both) the full url, or the endpoint part, must be given as
    an argument. The data is optional, and can be a JSON dict or a binary
    string. The msg shoul describe the action being performed and will be used
    to construct log messages and an exception message if needed.
    '''
    if endpoint:
        url = os.environ.get('INVENIO_SERVER') + endpoint
    data_type = 'json' if isinstance(data, (dict, list)) else 'octet-stream'
    headers = {'Content-type': 'application/' + data_type}
    if token := os.environ.get('INVENIO_TOKEN'):
        headers['Authorization'] = 'Bearer ' + token

    if os.environ.get('IGA_RUN_MODE') == 'debug':
        d = json.dumps(data, indent=2) if data_type == 'json' else ''
        log(f'doing {action} on {url}' + (f' with payload:\n{d}' if d else ''))

    # Construct a Python partial to gather some args for calling network().
    client = None
    if action == 'put':
        # 'put' => data is being uploaded, so we need to set longer timeouts.
        import httpx
        tmout = _network_timeout(data)
        timeout = httpx.Timeout(tmout, connect=10, read=tmout, write=tmout)
        client = httpx.Client(timeout=timeout, http2=True, verify=False)
    api_call = partial(net, action, url, client=client, headers=headers)

    # Now perform the actual network api call.
    try:
        if data:
            log(f'data payload size = {len(data)}')
            if data_type == 'json':
                response, error = api_call(json=data)
            else:
                response, error = api_call(content=data)
        else:
            response, error = api_call()
        if error:
            raise error
        response_json = response.json()
        if os.environ.get('IGA_RUN_MODE') == 'debug':
            log(f'got response:\n{json.dumps(response_json, indent=2)}')
        return response_json
    except KeyboardInterrupt:
        raise
    except commonpy.exceptions.NoContent:
        log(f'got no content for {endpoint}')
        return None
    except commonpy.exceptions.CommonPyException as ex:
        # Invenio responds w/ code 400 if the token is invalid but the msg in
        # the response ("Referer checking failed") is confusing. Let's do better.
        if response.status_code == 400:
            raise InvenioRDMError(f'Failed to {msg}. The server rejected the'
                                  ' request, possibly because of an invalid'
                                  ' InvenioRDM token.')
        else:
            raise InvenioRDMError(f'Failed to {msg}. {str(ex).capitalize()}')
    except Exception:
        raise


def _network_timeout(data):
    '''Return a timeout value (in seconds) for writing the given data string.

    This uses the value in the environment variable IGA_NETWORK_TIMEOUT, if
    given. If no explicit timeout value has been given, this calculates an
    adaptive timeout value based on the size of the data, using a custom
    heuristic invented by the author based on his experiences with a
    slowish network.
    '''
    if given_timeout := os.environ.get('IGA_NETWORK_TIMEOUT'):
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
