'''
name_utils.py: utilities for dealing with people's names

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2024 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

from   collections import defaultdict
from   functools import cache
import re
import regex
from   sidetrack import log

from iga.data_utils import constant_factory


# Internal module variables.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

_SPACY = {}
'''Cache for spaCy NLP models, so we don't have to load them more than once.'''

_SPACY_MODELS = defaultdict(constant_factory('en_core_web_trf'))
'''Mapping from BCP-47-style language codes to spaCy NLP models.'''

_SPACY_MODELS.update({
    'ja': 'ja_ginza_electra',
    'ko': 'ko_core_news_lg',
    'zh': 'zh_core_web_lg',
})

_HIRAGANA_KATAKANA_REGEX = regex.compile(r'[ぁ-ゖ゛-ゟ゠-ヿ]')
'''Regular expression matching Japanese Hiragana and Katakana characters.'''

# See https://www.unicode.org/iso15924/iso15924-codes.html
_CJK_CHARACTERS_REGEX = regex.compile(r'[\p{IsHani}\p{IsHira}\p{IsKana}\p{IsBopo}\p{IsHang}]')
'''Regular expression matching Unicode ranges for all CJK characters.'''

_CJK_SURNAMES_REGEX = None
'''Cache for common person names in CJK scripts, so that we don't have to load
them more than once.'''

_CJK_SURNAMES_FILENAME = 'surnames.p'
'''Pickled CaseFoldSet in iga/data containing common Chinese, Japanese, and
Korean person names.'''

_ORGANIZATIONS = None
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

_NON_PERSON_ELEMENTS = {
    # Possessive expressions are almost never part of a person's name.
    "'s",
    # People who hyphenate their names don't put spaces around the hyphen.
    ' - ',
    ' – ',                              # en-dash
    ' — ',                              # em-dash
    # Some company names have these.
    '&',
    '+',
}
'''Items used as part of a filter to rule out person names.'''


# Exported module functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@cache
def is_person(name):
    '''Try to guess whether the given string is likely to be a person's name.

    It is impossible to reliably determine with 100% accuracy whether a given
    string of characters represents the name of a person and not, say, the
    name of a company or product. This function makes a best-effort guess
    using heuristics in combination with methods from natural language
    processing (NLP), but it will sometimes make mistakes.

    This function is designed with the assumption that its input is already
    expected to be a name, and it only needs to guess whether it is the name
    of a person or not.
    '''
    if not name:
        return False

    # If every part is a number, it's not a name.
    name_tokens = re.split(r'[-\s:]+', name)
    if all(token.isdigit() for token in name_tokens):
        log(f'{name} consists of just numbers => not a person')
        return False

    # The NLP approaches use different trained models for different languages.
    # We switch depending on the script used in the name.
    plain_text_part = _plain_name(name)
    if len(plain_text_part) > 0:
        # Either it's all Latin script, or mix of Latin & CJK characters. If a
        # mix, it's likely both an English and CJK version of the same thing.
        # (E.g., someone might write their name in Chinese in parentheses after
        # an English version.) If that's the case, we use only the non-CJK part.
        log(f'Latin-only portion of name is "{plain_text_part}"')
        return is_western_name(plain_text_part)
    elif contains_cjk(name):
        # Cleaning removed everything b/c the string contained only CJK chars.
        log(f'{name} contains only CJK characters')
        return is_cjk_name(name)
    else:
        log(f'cleaning {name} resulted in empty string => returning False')
        return False


def is_western_name(name):
    '''Try to guess whether the given string is a person's name. The "name"
    string is assumed to have been cleaned and contains no CJK characters.
    '''
    # A string like "Joe's Foobar" is never a person's name.
    if any(element in name for element in _NON_PERSON_ELEMENTS):
        log(f'{name} contains non-person elements => not a person')
        return False

    # The ML-based NER systems sometimes mislabel company names, so we start
    # by checking against a list of known organization names. If we recognize
    # a known org name, then it's not a person's name.
    global _ORGANIZATIONS
    if not _ORGANIZATIONS:
        _load_organizations()
    if name in _ORGANIZATIONS:
        log(f'recognized {name} as a known organization => not a person')
        return False

    # The easy checks failed, so looks like we have to load the NLP systems.
    global _SPACY
    if 'en' not in _SPACY:
        _load_spacy('en')
    spacy_loaded = ('en' in _SPACY)

    # Check that we successfully loaded spaCy & fall back to PP if we didn't.
    decision = None
    if spacy_loaded:
        spacy_model = _SPACY['en']
        decision = person_according_to_spacy(name, spacy_model)
    if decision is None:
        # spaCy does the best job, but sometimes it doesn't produce any tags.
        # We fall back to PP in that case.
        decision = person_according_to_pp(name)
    log(f'final decision: is_person({name}) = {decision}')
    return decision


def is_cjk_name(name):
    '''Try to guess whether the given string is a person's name. The "name"
    string is assumed to contain only CJK characters.
    '''
    # As is the case for Western names, there is no perfect discriminator for
    # Chinese, Japanese, or Korean names. The situation here is slightly
    # helped, however, by naming traditions in China, Japan, and Korea: a
    # large fraction of the population shares common last names. So, we start
    # by testing the string for a match against these common names.
    global _CJK_SURNAMES_REGEX
    if not _CJK_SURNAMES_REGEX:
        _load_cjk_names()
    if _CJK_SURNAMES_REGEX.search(name):
        log(f'final decision: is_person({name}) = True (contains known surname)')
        return True

    # Not a recognized name, so load an appropriate NLP model and try it.
    global _SPACY
    lang = detected_language(name)
    if lang not in _SPACY:
        _load_spacy(lang)
    spacy_loaded = (lang in _SPACY)
    decision = False
    if spacy_loaded:
        spacy_model = _SPACY[lang]
        decision = person_according_to_spacy(name, spacy_model)
        decision = False if decision is None else decision
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
    name = _plain_name(name)
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
            guessed_prefix = (from_pp[0].get('PrefixOther', '')
                              or from_pp[0].get('PrefixMarital', ''))
            has_bad_prefix = guessed_prefix.replace('.', '') not in _COMMON_PREFIXES
            has_corp_key = any(key.startswith('Corp') for key in from_pp[0].keys())
            if guessed_type != 'Person' or has_bad_prefix or has_corp_key:
                from_pp = pp.tag(name, type='person')
                log(f'probablepeople 2nd result: {str(from_pp)}')
                guessed_prefix = (from_pp[0].get('PrefixOther', '')
                                  or from_pp[0].get('PrefixMarital', ''))
                if guessed_prefix.replace('.', '') not in _COMMON_PREFIXES:
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
    return _CJK_CHARACTERS_REGEX.search(text)


# Miscellaneous helper functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def _plain_name(name):
    from iga.text_utils import without_html
    # Remove any HTML tags there might be left.
    name = without_html(name)
    # Remove parenthetical text like "Somedude [somedomain.io]".
    name = re.sub(r"\(.*?\)|\[.*?\]", "", name)
    # Replace typographical quotes with regular quotes.
    name = name.replace('‘', "'")
    name = name.replace('’', "'")
    name = name.replace('“', '"')
    name = name.replace('”', '"')
    # Make sure periods are followed by spaces.
    name = name.replace('.', '. ')
    # Remove most non-Latin characters.
    name = regex.sub(r"[^-&+ .'\"–—\p{IsLatn}]", '', name)
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
    # is undesired behavior for our purposes.
    return ' '.join(word[0].upper() + word[1:] for word in name.split())


def _load_cjk_names():
    global _CJK_SURNAMES_REGEX
    from os.path import dirname, abspath, join
    import pickle
    here = dirname(abspath(__file__))
    name_file = join(here, f'data/{_CJK_SURNAMES_FILENAME}')
    log(f'loading {name_file} – this may take some time')
    names_set = None
    with open(name_file, 'rb') as f:
        names_set = pickle.load(f)
    _CJK_SURNAMES_REGEX = regex.compile(r'\L<alternatives>', alternatives=names_set)


def _load_organizations():
    global _ORGANIZATIONS
    from os.path import dirname, abspath, join
    import pickle
    here = dirname(abspath(__file__))
    org_file = join(here, f'data/{_ORGANIZATIONS_FILENAME}')
    log(f'loading {org_file} – this may take some time')
    with open(org_file, 'rb') as f:
        _ORGANIZATIONS = pickle.load(f)


def _load_spacy(lang='en'):
    global _SPACY
    import spacy
    model = _SPACY_MODELS[lang]
    try:
        log(f'trying to load spaCy model {model} – this may some time')
        _SPACY[lang] = spacy.load(model)
    except KeyboardInterrupt:
        raise
    except (OSError, ValueError):
        log(f'spaCy {model} not yet installed, so doing one-time download')
        if _successful_spacy_download(model):
            log('spaCy model has been successfully downloaded')
            _SPACY[lang] = spacy.load(model)
        else:
            log(f'unable to get download {model} – spaCy will not be usable')
    else:
        log(f'finished loading spaCy pipeline for {lang} language')


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


def person_according_to_spacy(name, spacy_model):
    try:
        parsed = spacy_model(name)
        if parsed.ents:
            entity_types = [entity.label_ for entity in parsed.ents]
            log(f'spaCy entity types for {name}: {entity_types}')
            return any(t.lower() in ('person', 'ps') for t in entity_types)
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


def detected_language(text):
    '''Guess whether the language is Chinese, Japanese, or Korean.'''
    # Names in CJK languages can be as short as a single character. Most
    # language-detection methods fail on such short strings. The best we can
    # do is apply a combination of heuristics.

    # Text containing Hiragana and/or Katakana is almost certainly Japanese.
    if _HIRAGANA_KATAKANA_REGEX.search(text):
        log('detected hiragana or katakana characters => language is ja')
        return 'ja'

    # Text containing Hangul characters is almost certainly Korean.
    from jamo import is_hangul_char
    if any(is_hangul_char(c) for c in text):
        log('detected hangul characters => language is ko')
        return 'ko'

    # OK, the easy tests failed. The name could still be in any of the CJK
    # languages b/c they all can use Han characters. Guessing the language
    # based on a couple of characters is known to be impossible to do 100%
    # reliably. In my testing, Lingua was more accurate than GCLD3, FastText,
    # langdetect, Polyglot, & spaCy overall, but it's far from perfect. The
    # approach here is: if Lingua reports anything but CJK, default to Chinese.
    from lingua import Language
    from lingua import LanguageDetectorBuilder as LDB
    lg = LDB.from_all_languages().with_preloaded_language_models().build()
    lg_mapping = {Language.CHINESE: 'zh',
                  Language.JAPANESE: 'ja',
                  Language.KOREAN: 'ko'}
    lang = lg.detect_language_of(text)
    log(f'Lingua reports {lang} as language of {text}')
    return lg_mapping[lang] if lang in lg_mapping else 'zh'
