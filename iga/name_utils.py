'''
name_utils.py: utilities for dealing with people's names

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2023 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

from sidetrack import log


# Exported module functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def split_name(name):
    '''Split a name into given name & surname.

    To be honest, trying to split names automatically into parts is not only
    impossible in general -- it's also undesirable: not all cultures use names
    with only first and/or last name components, or just one last name, or in
    the same order as Western names, etc. However, we have no choice for IGA
    because InvenioRDM's record format only supports split first & last names.
    '''
    # The approach taken here is roughly:
    #  1) strip non-Latin characters and non-alpha characters from the string
    #  2) if the result is only a single word, treat it as a surname only
    #  3) invoke a machine learning-based name parser (ProbablePeople) to do
    #     a best-effort attempt at splitting the name into given + surname
    #  4) PP is prone to failures on some names, so if it fails, fall back to
    #     using a different name parser (nameparser) that doesn't split names
    #     quite as correctly as PP, but is better than nothing.

    log('splitting name ' + name)
    name = _cleaned_name(name)
    if len(name.split(' ')) == 1:
        # Only one word in the name. Either it is really a single name (e.g.,
        # in cultures where people have single names) or someone is being cute.
        log('treating single name as the family name')
        given = ''
        surname = name
    else:
        try:
            log('trying to split name using probablepeople')
            import probablepeople as pp
            from_pp = pp.tag(name)
            # PP gets better results if you DON'T supply the 'type' parameter.
            # (I don't know why.) Use that 1st, unless it guesses wrong about
            # the type, in which case, we run it again using type=person.
            if from_pp[1] != 'Person':
                from_pp = pp.tag(_cleaned_name(name), type='person')
            parsed = from_pp[0]
            # If it found initials instead of full names, use those.
            if parsed.get('FirstInitial', ''):
                given = parsed.get('FirstInitial')
            else:
                # Get rid of periods at the end, in case someone got cute.
                given = parsed.get('GivenName', '').rstrip('.')

            # For some reason, it seems the InvenioRDM records include the
            # middle names as part of the first/given names, so:
            if parsed.get('MiddleInitial', ''):
                given += (' ' + parsed.get('MiddleInitial'))
            elif parsed.get('MiddleName', ''):
                given += (' ' + parsed.get('MiddleName'))

            if parsed.get('LastInitial', '') and not parsed.get('Surname', ''):
                surname = parsed.get('LastInitial').title()
            else:
                surname = parsed.get('Surname', '')
        except Exception:                   # noqa: PIE786
            log(f'switching to nameparser b/c probablepeople failed on "{name}"')
            from nameparser import HumanName
            parsed = HumanName(name)
            # (Noted above) InvenioRDM includes middle name as part of 1st name:
            given = parsed.first + ' ' + parsed.middle
            surname = parsed.last

    given = _upcase_first_letters(given)
    if _plain_word(surname):
        surname = surname.title()
    surname = surname.strip()

    return (given, surname)


def flattened_name(name):
    '''Return name as a string even if it's a list and not a simple string.'''
    return ' '.join(part for part in name) if isinstance(name, list) else name


# Miscellaneous helper functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def _cleaned_name(name):
    import re
    import demoji
    # Remove parenthetical text like "Somedude [somedomain.io]".
    name = re.sub(r"\(.*?\)|\[.*?\]", "", name)
    # Remove CJK characters because the name parsers can't handle them.
    # This regex is from https://stackoverflow.com/a/2718268/743730
    name = re.sub(u'[⺀-⺙⺛-⻳⼀-⿕々〇〡-〩〸-〺〻㐀-䶵一-鿃豈-鶴侮-頻並-龎]', '', name)
    # Remove miscellaneous weird characters if there are any.
    name = demoji.replace(name)
    name = re.sub(r'[~`!@#$%^&*_+=?<>(){}|[\]]', '', name)
    # Replace typographical quotes with regular quotes, for PP's benefit.
    name = re.sub(r'[“”‘’]', '"', name)
    # Make sure periods are followed by spaces.
    name = name.replace('.', '. ')
    # Normalize runs of multiple spaces to one.
    name = re.sub(r' +', ' ', name)
    return name.strip()                 # noqa PIE781


def _plain_word(name):
    return (' ' not in name
            and not any(str.isdigit(c) for c in name)
            and (all(str.isupper(c) for c in name)
                 or not any(str.isupper(c) for c in name[1:])))


def _upcase_first_letters(name):
    # Python's .title() will downcase the letters after the 1st letter, which
    # is undesired behavior for the situation where we need this.
    return ' '.join(word[0].upper() + word[1:] for word in name.split())
