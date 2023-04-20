'''
json_utils.py: utilities for working with JSON

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2023 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

import dirtyjson
from   sidetrack import log


# Internal module constants.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

_MAX_RECURSION_DEPTH = 4
'''Maximum times we will retry parsing the json content.'''


# Exported module functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def partial_json(content, skip_line=None, recursion=0):
    '''Parse content as JSON, skipping invalid lines, and return a dict.

    The approach is simple-minded: try to parse the file, and if an error
    occurs, skip the line where the error was first detected. Sometimes an
    error affects online one line and the rest of the JSON content may be
    usable. Other times, skipping a line will result in completely unparseable
    JSON, so the result of using this function may be an empty JSON.
    '''
    if skip_line:
        log(f'skipping line {skip_line} in JSON content and retrying')
        # This is an embarrassingly simple-minded approach. Maybe someday we
        # can make something better and more performant, but for now ...
        content = content.split('\n')
        content = content[:skip_line - 2] + content[skip_line - 1:]
        content = '\n'.join(content)
    try:
        return dict(dirtyjson.loads(content))
    except KeyboardInterrupt:
        raise
    except dirtyjson.error.Error as ex:
        # Do we have a line number?
        log('error parsing JSON: ' + str(ex))
        if line := getattr(ex, 'lineno'):
            if recursion <= _MAX_RECURSION_DEPTH:
                return partial_json(content, line, recursion + 1)
            else:
                log('exceeded recursion depth and admitting failure')
                return {}
    return {}
