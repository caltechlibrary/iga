'''
text_utils.py: misc. utilities for doing stuff with text

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2023 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''


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
    except KeyboardInterrupt as ex:
        raise ex
    except Exception:                   # noqa PIE786
        return text
