'''
ror.py: utilities for getting information from ROR

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2023 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

from   commonpy.network_utils import net
import json
from   sidetrack import log

from   iga.id_utils import detected_id


# Exported module functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def name_from_ror(ror):
    ror = detected_id(ror) if ror.startswith('http') else ror
    log('contacting ROR.org for ROR organizations data about ' + ror)
    data_url = f'https://api.ror.org/organizations/{ror}'
    response, error = net('get', data_url)
    if error:
        log('failed to get ROR data for ' + ror)
        return ('', '')

    json_dict = json.loads(response.text)
    return json_dict.get('name', '')
