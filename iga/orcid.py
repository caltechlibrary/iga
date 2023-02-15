'''
orcid.py: simple functions for interfacing to ORCID

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2023 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

from   commonpy.exceptions import CommonPyException
from   commonpy.network_utils import net
import json
from   sidetrack import log

from iga.id_utils import detected_id
from iga.name_utils import split_name


# Exported module functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def name_from_orcid(orcid):
    '''Return a (first name, family name) tuple for the given ORCID id.

    The identifier can be a pure ORCID id like 0000-0001-9105-5960, or it can
    be in the form of a URL like https://orcid.org/0000-0001-9105-5960.

    ORCID records often provide split family/given names, but not always. If a
    given user's name is not available in a split form but a name is available
    in the form of an undifferentiated name, attempt to split the name using
    methods in IGA's name_utils module.
    '''
    if not orcid or not isinstance(orcid, str):
        return ('', '')
    orcid = detected_id(orcid) if orcid.startswith('http') else orcid
    log('contacting ORCID for record for ' + orcid)
    data_url = f'https://orcid.org/{orcid}/public-record.json'
    try:
        response, error = net('get', data_url)
        if error:
            log(f'failed to get ORCID data for {orcid}: ' + str(error))
            return ('', '')
        json_dict = json.loads(response.text)
    except json.JSONDecodeError as ex:
        log('unable to decode response from orcid.org API: ' + str(ex))
        return ''
    except CommonPyException as ex:
        log('failed to communicate with orcid.org: ' + str(ex))
        return ''

    given = ''
    family = ''
    if names := json_dict.get('names', {}):
        # People often set a creditName value. This would be preferred for our
        # uses (to wit, giving credit for someone's work) except that the field
        # is a single string and not separated into parts. So we resort to the
        # following: if creditName is present, we hand it to our name splitter
        # and use just the first name part of the result because it's the part
        # we suspect will be preferred over the givenNames field value. In any
        # case, we always use the familyName part of the ORCID names dict.
        if (cn := names.get('creditName', {})) and (value := cn.get('value', '')):
            log('record has a creditName value: ' + value)
            given, family = split_name(value)
            if family_dict := names.get('familyName', {}):
                family = family_dict.get('value')
            log('final composite name: ' + given + ' ' + family)
        else:
            log('record does not have a creditName value')
            if given_dict := names.get('givenNames', {}):
                given = given_dict.get('value', '')
            if family_dict := names.get('familyName', {}):
                family = family_dict.get('value')
            log('values from given and family names: ' + given + ' ' + family)

        # In some societies, people only have a single name. If we get that
        # much from the name field, we assume we're done.
        if family:
            return (given, family)

    # The "names" object is empty for some reason. See if there's another name.
    if other := json_dict.get('otherNames', {}):
        # Yes, this dict has a nested dict with the same name. Don't ask me why.
        for item in other.get('otherNames', []):
            name = item.get('content', '') or item.get('sourceName', '')
            if name:
                log('found otherNames dict in ORCID data with name ' + name)
                given, family = split_name(name)
                break
            else:
                log('found otherNames dict in ORCID data without a name')
        else:
            log('failed to find nested otherNames dict in ORCID data')
    return (given, family)
