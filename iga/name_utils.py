'''
name_utils.py: utilities for dealing with people's names

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2023 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

from commonpy.data_structures import CaseFoldSet
from functools import cache
from sidetrack import log


# Internal module variables.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# The following is based on an answer posted to Stack Overflow on 2018-10-16
# by user "9999years" at https://stackoverflow.com/a/52837006/743730.
CJK_RANGES = [
    (0x4E00, 0x62FF),
    (0x6300, 0x77FF),
    (0x7800, 0x8CFF),
    (0x8D00, 0x9FCC),
    (0x3400, 0x4DB5),
    (0x20000, 0x215FF),
    (0x21600, 0x230FF),
    (0x23100, 0x245FF),
    (0x24600, 0x260FF),
    (0x26100, 0x275FF),
    (0x27600, 0x290FF),
    (0x29100, 0x2A6DF),
    (0x2A700, 0x2B734),
    (0x2B740, 0x2B81D),
    (0x2B820, 0x2CEAF),
    (0x2CEB0, 0x2EBEF),
    (0x2F800, 0x2FA1F)
]
'''List of codepoint ranges for CJK characters in Unicode. Tuples indicate
the bottom and top of the range, inclusive.'''

_NON_PERSON_ELEMENTS = {
    # Possessive expressions are almost never part of a person's name.
    "'s",
    # People who hyphenate their names don't put spaces around the hyphen.
    ' - ',
    ' – ',                              # en-dash
    ' — ',                              # em-dash
}
'''Items used as part of a filter to rule out person names.'''

_NLP = {}
'''Cache for the spaCy model so that we don't have to load it more than once.'''

_ORGANIZATIONS = {}
'''Cache for the set of well-known company names.'''

_ORGANIZATIONS_FILENAME = 'org-names.p'
'''Pickled CaseFoldSet in iga/data containing organization names.'''

_COMMON_PREFIXES = [
    '',
    'Dame',
    'Dr',
    'Fr',
    'Imām',
    'Lady',
    'Lord',
    'Messrs',
    'Miss',
    'Mr',
    'Mrs',
    'Ms',
    'Mx',
    'Pr',
    'Prof',
    'Professor',
    'Rabbi',
    'Revd',
    'Roshi',
    'Sensei',
    'Sir',
]


# Exported module functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

# https://stackoverflow.com/questions/54334304/spacy-cant-find-model-en-core-web-sm-on-windows-10-and-python-3-5-3-anacon
# import spacy.cli
# spacy.cli.download("en_core_web_trf")
# spacy.cli.download("zh_core_web_trf")

@cache
def is_person(name):
    '''Try to guess whether the given string is a person's name.

    In the most general case, it is impossible to reliably determine whether a
    given string of characters represents the name of a person and not, say,
    the name of a company or product. This function makes a best-effort guess
    using heuristics in combination with methods from natural language
    processing (NLP), but it will sometimes make mistakes.

    This function is designed with the assumption that its input is already
    expected to be a name, and it only needs to make the determination of
    whether it is the name of a person or not.
    '''
    if not name:
        return False

    # A string like "Joe's Foobar" is not a name.
    if any(item in name for item in _NON_PERSON_ELEMENTS):
        log(f'{name} contains non-person elements => not a person')
        return False

    # If the input contains a mix of Latin and CJK characters, it's likely to
    # contain both an English and CJK version of the same thing. (E.g.,
    # someone might write their name in Chinese in parentheses after an English
    # version.) If that's the case, we use only the non-CJK part if there is
    # one. If there are no CJK characters, we always use the cleaned version.
    charset = 'cjk' if contains_cjk(name) else 'default'
    log(f'{name} uses the {charset} charset')
    cleaned = _cleaned_name(name)
    if charset == 'default' or len(cleaned) > 0:
        log(f'using cleaned version of name: {cleaned}')
        name = cleaned
    if not name:
        # Cleaning removed everything.
        log(f'cleaning {name} resulted in an empty string => returning False')
        return False

    # Reject names whose every part is a number.
    import re
    name_tokens = re.split(r'[-\s:]+', name)
    if all(token.isdigit() for token in name_tokens):
        log(f'{name} consists of just numbers => not a person')
        return False

    # The ML-based NER systems sometimes mislabel company names, so we start
    # by checking against a list of known organization names.
    global _ORGANIZATIONS
    if not _ORGANIZATIONS:
        _load_organizations()
    if name in _ORGANIZATIONS:
        log(f'recognized {name} as a known organization => not a person')
        return False

    # Delay loading the ML systems until needed because they take long to load.
    # We check we succeded in loading it & fall back to other things if not.
    global _NLP
    if charset not in _NLP:
        _load_spacy(charset)
    spacy_loaded = (charset in _NLP)

    def person_according_to_spacy(name):
        try:
            parsed = _NLP[charset](name)
            if parsed.ents:
                entity_type = parsed.ents[0].label_
                log(f'spaCy [{charset}] entity type for {name}: {entity_type}')
                return (entity_type == 'PERSON')
            else:
                log(f'spaCy did not return entity labels for {name}')
                # Note the return is None, not False, so caller can test.
                return None
        except KeyboardInterrupt:
            raise
        except Exception as ex:             # noqa: PIE786
            log('unable to use spaCy due to error: ' + str(ex))
        return False

    def person_according_to_pp(name):
        import probablepeople as pp
        try:
            from_pp = pp.tag(name)
            log(f'entity type according to PP for {name}: {from_pp[1]}')
            return (from_pp[1] == 'Person')
        except KeyboardInterrupt:
            raise
        except Exception:                 # noqa: PIE786
            # PP sometimes fails with an exception.
            log(f'probablepeople failed for {name}')
        return False

    # Check that we successfully loaded spaCy & fall back to PP if we didn't.
    decision = None
    if spacy_loaded:
        decision = person_according_to_spacy(name)
    if decision is None:
        # spaCy does the best job, but sometimes it doesn't produce any tags.
        # We fall back to PP in that case.
        decision = person_according_to_pp(name)
    log(f'final decision: is_person({name}) = {decision}')
    return decision


@cache
def split_name(name):
    '''Split a name into given name & surname.

    Note: trying to split names automatically into parts is not only impossible
    in general -- it's also undesirable: not all cultures use names with only
    first and/or last name components, or just one last name, or in the same
    order as Western names, etc. However, we have no choice for IGA because
    InvenioRDM's record format only supports split first & last names.
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

            # PP gets better results if you DON'T supply the 'type' parameter.
            # (I don't know why.) Try it that way first, let it guess the type,
            # and if it guesses wrong, try it again but with the type that time.
            from_pp = pp.tag(name)
            log(f'probablepeople initial result: {str(from_pp)}')
            guessed_type = from_pp[1]
            guessed_prefix = from_pp[0].get('PrefixOther', '')
            has_bad_prefix = guessed_prefix not in _COMMON_PREFIXES
            has_corp_key = any(key.startswith('Corp') for key in from_pp[0].keys())
            if guessed_type != 'Person' or has_bad_prefix or has_corp_key:
                from_pp = pp.tag(name, type='person')
                log(f'probablepeople 2nd result: {str(from_pp)}')
                guessed_prefix = from_pp[0].get('PrefixOther', '')
                if guessed_prefix not in _COMMON_PREFIXES:
                    # This is a sign something is still wrong. Give up on PP.
                    raise Exception
            parsed = from_pp[0]

            # If it found initials instead of full names, use those.
            if parsed.get('FirstInitial'):
                given = parsed.get('FirstInitial')
            else:
                # Get rid of periods at the end, in case someone got cute.
                given = parsed.get('GivenName', '').rstrip('.')

            # InvenioRDM wants middle names to be part of the first/given names:
            if middle := (parsed.get('MiddleInitial') or parsed.get('MiddleName')):
                given += (' ' + middle)

            # If we only have a last initial, then that's all we can use.
            if parsed.get('LastInitial') and not parsed.get('Surname'):
                surname = parsed.get('LastInitial', '').title()
            else:
                surname = parsed.get('Surname', '')

            # If we didn't find a given name but the surname has a space, use
            # it as a split point & take all but last word as the given name.
            if not given and ' ' in surname:
                split = surname.split(' ')
                surname = split.pop()
                given = ' '.join(split)
        except KeyboardInterrupt:
            raise
        except Exception:                   # noqa: PIE786
            log(f'switching to nameparser b/c probablepeople failed on "{name}"')
            from nameparser import HumanName
            parsed = HumanName(name)
            # (Noted above) InvenioRDM includes middle name as part of 1st name:
            given = parsed.first + ' ' + parsed.middle
            surname = parsed.last

    given = _first_letters_upcased(given)
    if _plain_word(surname):
        surname = surname.title()
    surname = surname.strip()

    log(f'final name splitting result: ({given}, {surname})')
    return (given, surname)


def flattened_name(name):
    '''Return name as a string even if it's a list and not a simple string.'''
    return ' '.join(part for part in name) if isinstance(name, list) else name


def contains_cjk(text):
    '''Return True if text contains any character in the CJK character sets.'''
    def is_cjk(char):
        char = ord(char)
        return any(char >= bottom and char <= top for bottom, top in CJK_RANGES)

    return any(map(is_cjk, text))


# Miscellaneous helper functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def _cleaned_name(name):
    import re
    import demoji
    from iga.text_utils import without_html
    # Remove any HTML tags there might be left.
    name = without_html(name)
    # Remove parenthetical text like "Somedude [somedomain.io]".
    name = re.sub(r"\(.*?\)|\[.*?\]", "", name)
    # Remove CJK characters because the name parsers can't handle them.
    # This regex is from https://stackoverflow.com/a/2718268/743730
    name = re.sub(u'[⺀-⺙⺛-⻳⼀-⿕々〇〡-〩〸-〺〻㐀-䶵一-鿃豈-鶴侮-頻並-龎]', '', name)
    # Remove miscellaneous weird characters if there are any.
    name = demoji.replace(name)
    name = re.sub(r'[~`!@#$%^&*_+=?<>(){}|[\]¡¿]', '', name)
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


def _first_letters_upcased(name):
    # Python's .title() will downcase the letters after the 1st letter, which
    # is undesired behavior for the situation where we need this.
    return ' '.join(word[0].upper() + word[1:] for word in name.split())


def _load_organizations():
    global _ORGANIZATIONS
    from os.path import dirname, abspath, join
    import pickle
    here = dirname(abspath(__file__))
    org_file = join(here, f'data/{_ORGANIZATIONS_FILENAME}')
    log(f'loading {org_file} – this may take some time')
    with open(org_file, 'rb') as f:
        _ORGANIZATIONS = pickle.load(f)


def _load_spacy(charset):
    global _NLP
    import spacy
    model = 'zh_core_web_trf' if charset == 'cjk' else 'en_core_web_trf'
    try:
        log(f'try to load spaCy model {model} – this may some time')
        _NLP[charset] = spacy.load(model)
    except KeyboardInterrupt:
        raise
    except OSError:
        log(f'spaCy {model} not yet installed, so doing one-time download')
        if _successful_spacy_download(model):
            log('spaCy model has been successfully downloaded')
            _NLP[charset] = spacy.load(model)
        else:
            log(f'unable to get download {model} – spaCy will not be usable')
    else:
        log(f'finished loading spaCy pipeline for {charset} charset')


def _successful_spacy_download(model):
    from spacy.cli import download
    from subprocess import SubprocessError
    try:
        download(model)
    except KeyboardInterrupt:
        raise
    except (FileNotFoundError, SubprocessError) as ex:
        log(f'error trying to download spaCy model {model}: {str(ex)}')
    else:
        return True
    return False
