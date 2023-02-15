'''
orcid.py: simple functions for interfacing to ORCID

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2023 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

from   commonpy.network_utils import net
import json
from   sidetrack import log

from iga.id_utils import detected_id
from iga.name_utils import split_name


# Exported module functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def name_from_orcid(orcid):
    '''Contact ORCID to get the public record for a given ORCID id.'''
    orcid = detected_id(orcid) if orcid.startswith('http') else orcid
    log('contacting ORCID for record for ' + orcid)
    data_url = f'https://orcid.org/{orcid}/public-record.json'
    response, error = net('get', data_url)
    if error:
        log(f'failed to get ORCID page for {orcid} due to error: ' + str(error))
        return ('', '')

    json_dict = json.loads(response.text)
    given = ''
    family = ''
    if names := json_dict.get('names', {}):
        log('found names dict in ORCID data')
        # When broken out into parts in ORCID, the first name often omits
        # middle names and middle initials, yet these are often included in the
        # value of a separate "creditName" field. Frustratingly, that field is
        # a single string and not separated into parts, so we can't just use it
        # directly. We won't let that stop us, though. If creditName is
        # present, we hand it to our name splitter and use the first name from
        # that result (in the hopes that it will be more complete), and combine
        # that with the family name given in the ORCID record.
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
            log('values from given and family fields: ' + given + ' ' + family)
    elif other := json_dict.get('otherNames', {}):
        # Yes, it has a nested dict with the same name. Don't ask me why.
        for item in other.get('otherNames', []):
            name = item.get('content', '') or item.get('sourceName', '')
            if name:
                log('found otherNames dict in ORCID data with name ' + name)
                given, family = split_name(name)
                break
            else:
                log('found otherNames dict in ORCID data without a name field')
        else:
            log('failed to find nested otherNames dict in ORCID data')

    return (given, family)
