'''
data_utils.py: miscellaneous data-handling utilities.

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2023 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

from typing import Generator, Iterator


def deduplicated(_list):
    if not _list:
        return []
    elif isinstance(_list, Generator):
        return deduplicated(list(_list))
    elif isinstance(_list, Iterator):
        return deduplicated([x for x in _list])
    elif not isinstance(_list, list):
        return _list
    elif isinstance(_list[0], dict):
        # Python dicts are not hashable, so comparing them is difficult. One
        # approach would be to use a set of frozensets to help uniquefy
        # values, but frozenset alone doesn't handle nested dictionaries.
        # The following simple solution is O(n^2) -- bad for big sets, but
        # our uses in IGA are small, so this is sufficient.
        deduplicated_list = []
        seen = []
        for item in _list:
            if item not in seen:
                seen.append(item)
                deduplicated_list.append(item)
        return deduplicated_list
    else:
        from commonpy.data_utils import unique
        return unique(_list)


def similar_urls(url1, url2):
    return (
        url1 == url2
        or url1.rstrip('/') == url2
        or url1 == url2.rstrip('/')
        or url1.replace('http://', 'https://') == url2
        or url1.replace('https://', 'http://') == url2
        or url1.replace('http://', 'https://').rstrip('/') == url2
        or url1.replace('http://', 'https://') == url2.rstrip('/')
        or url1.replace('https://', 'http://').rstrip('/') == url2
        or url1.replace('https://', 'http://') == url2.rstrip('/')
    )
