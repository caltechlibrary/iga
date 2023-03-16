'''
data_utils.py: miscellaneous data-handling utilities.

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2023 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

from typing import Generator, Iterator


def deduplicated(lst):
    '''Return a copy of lst from which duplicate items have been removed.'''
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
    '''Return True if url1 is believed to be the same URL as url2.'''
    # I found things like urllib's urlparse and w3lib's canonicalize_url
    # unhelpful for this purpose. For example, for our cases we want to
    # assume https://foo.org/bar/ is the same as https://foo.org/bar, even
    # though by strict URL rules they're not. In the end I ended up doing this:
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
    '''Return a list made out of thing.

    If thing is a single object, then this returns [thing].
    If list is a list, Iterator or Generator, this simply returns thing.
    '''
    if not thing:
        return []
    return thing if isinstance(thing, (list, Iterator, Generator)) else [thing]


def cleaned_text(text):
    '''Return text that has been mildly cleaned up.

    Whitespace characters are normalized to single spaces, and period
    characters are followed by one space.
    '''
    # Get rid of embedded newlines and related characters.
    text = ' '.join(text.splitlines())
    # Normalize runs of multiple spaces to one.
    return ' '.join(text.split())


def without_html(text):
    '''Return the given text with HTML tags, if any, removed.'''
    from lxml import html
    try:
        return html.fromstring(text).text_content().strip()
    except Exception:                   # noqa PIE786
        return text
