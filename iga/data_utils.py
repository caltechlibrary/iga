'''
data_utils.py: miscellaneous data-handling utilities.

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2023 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

def deduplicated(_list):
    if not _list:
        return []
    elif not isinstance(_list, list):
        return _list
    elif isinstance(_list[0], dict):
        # Python dicts are not hashable, so comparing them is difficult.
        # Many implementations of a deduplication process use frozenset, but
        # frozenset alone doesn't handle nested dictionaries. The following
        # is not very elegant, nor efficient, but works for small data sizes.
        # Based in part on answer by Martijn Pieters posted to Stack Overflow
        # on 2014-12-09 at https://stackoverflow.com/a/27374412/743730
        from commonpy.data_utils import flattened
        deduplicated_list = []
        seen = set()
        for item in _list:
            if (item_flattened := frozenset(flattened(item))) not in seen:
                seen.add(item_flattened)
                deduplicated_list.append(item)
        return deduplicated_list
    else:
        from commonpy.data_utils import unique
        return unique(_list)
