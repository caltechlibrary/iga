'''
ror.py: utilities for getting information from ROR

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2023 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

import commonpy.exceptions
from   commonpy.network_utils import network
from   functools import cache
import json
import os
from   sidetrack import log

from   iga.id_utils import detected_id
from   iga.exceptions import InternalError


# Internal module constants.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

_MAX_RECURSION_DEPTH = 4
'''Maximum times a lookup will follow a successor link recursively.'''


# Exported module functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def name_from_ror(rorid, recursion=0):
    '''Return the name of an organization given a ROR identifier.

    The identifier can be a pure ROR id like 05dxps055, or it can be in the
    form of a URL like https://ror.org/05dxps055.

    If the ROR record for the given id is marked as withdrawn, look to see if
    the ROR entry lists a successor. If so, do a recursive lookup.
    '''
    if not rorid or not isinstance(rorid, str):
        return ''
    rorid = detected_id(rorid) if rorid.startswith('http') else rorid
    ror_dict = ror_data(rorid)

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

    name = ror_dict.get('name', '')
    log(f'ROR.org says organization {rorid} is named "{name}"')
    if ror_dict.get('status', '') != 'withdrawn':
        return name

    # If a record has been withdrawn, see if there's a link to an update.
    for related in ror_dict.get('relationships', []):
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


@cache
def ror_data(rorid):
    '''Return the data from ror.org for the given ROR id.'''
    if not rorid:
        return ''
    log(f'looking up ROR data about "{rorid}"')
    url = f'https://api.ror.org/organizations/{rorid}'
    try:
        data = network('get', url).json()
        if os.environ.get('IGA_RUN_MODE') == 'debug':
            log(f'data received for {rorid} from ror.org:\n{str(data)}')
        return data
    except KeyboardInterrupt:
        raise
    except commonpy.exceptions.NoContent:
        log(f'ROR.org returned no result for "{rorid}"')
    except commonpy.exceptions.CommonPyException as ex:
        log(f'could not get data from ROR.org for "{rorid}": ' + str(ex))
    except json.JSONDecodeError as ex:
        # This means we have to fix something.
        raise InternalError('Error trying to decode JSON from ror.org: ' + str(ex))
    except Exception:
        raise
    return ''
