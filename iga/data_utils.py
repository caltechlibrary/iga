'''
data_utils.py: miscellaneous data-handling utilities.

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2023 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

from typing import Generator, Iterator


def deduplicated(lst):
    if not lst:
        return []
    elif isinstance(lst, Generator):
        return deduplicated(list(lst))
    elif isinstance(lst, Iterator):
        return deduplicated([x for x in lst])
    elif not isinstance(lst, list):
        return lst
    elif isinstance(lst[0], dict):
        # Python dicts are not hashable, so comparing them is difficult. One
        # approach would be to use a set of frozensets to help uniquefy
        # values, but frozenset alone doesn't handle nested dictionaries.
        # The following simple solution is O(n^2) -- bad for big sets, but
        # our uses in IGA are small, so this is sufficient.
        deduplicated_list = []
        seen = []
        for item in lst:
            if item not in seen:
                seen.append(item)
                deduplicated_list.append(item)
        return deduplicated_list
    else:
        from commonpy.data_utils import unique
        return unique(lst)


def similar_urls(url1, url2):
    return (
        url1 == url2
        or url1.removesuffix('/') == url2
        or url1 == url2.removesuffix('/')
        or url1.replace('http://', 'https://') == url2
        or url1.replace('https://', 'http://') == url2
        or url1.replace('http://', 'https://').removesuffix('/') == url2
        or url1.replace('http://', 'https://') == url2.removesuffix('/')
        or url1.replace('https://', 'http://').removesuffix('/') == url2
        or url1.replace('https://', 'http://') == url2.removesuffix('/')
    )


def listified(thing):
    if not thing:
        return []
    return thing if isinstance(thing, (list, Iterator, Generator)) else [thing]


def cleaned_text(text):
    # Get rid of embedded newlines and related characters.
    text = ' '.join(text.splitlines())
    # Make sure periods are followed by spaces.
    text = text.replace('.', '. ')
    # Normalize runs of multiple spaces to one.
    return ' '.join(text.split())


def without_html(text):
    '''Return the given text with HTML tags, if any, removed.'''
    from lxml import html
    try:
        return html.fromstring(text).text_content().strip()
    except Exception:                   # noqa PIE786
        return text
