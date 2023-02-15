'''
ror.py: utilities for getting information from ROR

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2023 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

from   commonpy.exceptions import CommonPyException
from   commonpy.network_utils import net
import json
from   sidetrack import log

from   iga.id_utils import detected_id


# Internal module constants.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

_MAX_RECURSION_DEPTH = 4
'''Maximum times a lookup will follow a successor link recursively.'''


# Exported module functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def name_from_ror(rorid, recursion = 0):
    '''Return the name of an organization given a ROR identifier.

    The identifier can be a pure ROR id like 05dxps055, or it can be in the
    form of a URL like https://ror.org/05dxps055.

    If the ROR record for the given id is marked as withdrawn, look to see if
    the ROR entry lists a successor. If so, do a recursive lookup.
    '''
    if not rorid or not isinstance(rorid, str):
        return ''
    rorid = detected_id(rorid) if rorid.startswith('http') else rorid
    log('looking up ROR data about ' + rorid)
    data_url = f'https://api.ror.org/organizations/{rorid}'
    try:
        response, error = net('get', data_url)
        if error:
            log(f'failed to get ROR data for {rorid}: ' + str(error))
            return ''
        json_dict = json.loads(response.text)
    except json.JSONDecodeError as ex:
        log('unable to decode response from ror.org API: ' + str(ex))
        return ''
    except CommonPyException as ex:
        log('failed to communicate with ror.org: ' + str(ex))
        return ''

    # A record in ROR can be marked "inactive" or "withdrawn". If inactive,
    # we still return the name because for the purposes of IGA, it does not
    # matter if an org is inactive. (We can't tell why the user used that ROR
    # id -- perhaps they're backfilling old archives, and the value may make
    # sense in the context of what the user is doing.) On the other hand, if
    # the entry is marked "withdrawn" it means the record in ROR was created
    # in error; i.e., "withdrawn" is a property of the ROR record, not the
    # organization. In that case, we try to look for a new record in ROR.
    # For more information about record statuses, see the following page:
    # https://ror.readme.io/changelog/2022-12-01-organization-status-changes

    name = json_dict.get('name', '')
    log(f'ROR.org says organization {rorid} is named "{name}"')
    if not json_dict.get('status', '') == 'withdrawn':
        return name

    # If a record has been withdrawn, see if there's a link to an update.
    for related in json_dict.get('relationships', []):
        if related.get('type', '').lower() == 'successor':
            new_id = related.get('id', '')
            log(f'{rorid} marked as withdrawn; its successor is ' + new_id)
            if recursion <= _MAX_RECURSION_DEPTH:
                log('doing a recursive lookup on ' + new_id)
                return name_from_ror(new_id, recursion + 1)
            else:
                log('recursion depth exceeded; not continuing ROR lookups')
                return ''
    else:
        log(f'{rorid} marked as withdrawn but ROR lists no successor')
        return ''