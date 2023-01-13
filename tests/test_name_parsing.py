# =============================================================================
# @file    test_name_parsing.py
# @brief   Py.test cases for parts of record.py
# @created 2022-12-23
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/iga
# =============================================================================

from collections import namedtuple
from iga.record import _cleaned_name

Name = namedtuple('Name', 'first middle last')

RAW_NAMES = [
    ('偏右', ''),
    ('王爵nice', 'nice'),
    ('勾三股四', ''),
    ('TZ | 天猪', 'TZ'),
    ('Mu-An ✌️ Chiou', 'Mu-An Chiou'),
]

PARSED_NAMES = [
    ('Mike Hucka', Name(first='Mike', middle='', last='Hucka')),
    ('Rafael França', Name(first='Rafael', middle='', last='França')),
    ('王爵nice', Name(first='', middle='', last='nice')),
    ('Wladimir J. van der Laan', Name(first='Wladimir', middle='J.', last='van der Laan')),
    ('Mu-An ✌️ Chiou', Name(first='Mu-An', middle='', last='Chiou')),
    ('PatrickJS [tipe.io]', Name(first='', middle='', last='PatrickJS')),
    ('Jose Diaz-Gonzalez', Name(first='Jose', middle='', last='Diaz-Gonzalez')),
    ('TJ Holowaychuk', Name(first='TJ', middle='', last='Holowaychuk')),
    ('Ian Storm Taylor', Name(first='Ian', middle='Storm', last='Taylor')),
    ('Dr Nic Williams', Name(first='Nic', middle='', last='Williams')),
    ("Matthew Weier O'Phinney", Name(first='Matthew', middle='', last="Weier O'Phinney")),
    ('TZ | 天猪', Name(first='', middle='', last='TZ')),
    ('Martin Luther King, Jr.', Name(first='Martin', middle='Luther', last='King')),
    ('Carla Rodriguez de García', Name(first='Carla', middle='', last='Rodriguez de García')),
    ('J. Robert Oppenheimer', Name(first='J.', middle='Robert', last='Oppenheimer')),
    ('Jean-Jacques Rousseau', Name(first='Jean-Jacques', middle='', last='Rousseau')),
    ('Miguel de Cervantes', Name(first='Miguel', middle='', last='de Cervantes')),
    ("Weir O'Phinney", Name(first='Weir', middle='', last="O'Phinney")),
    ('Iuri de Silvio', Name(first='Iuri', middle='', last='de Silvio')),
    ('Miguel de Val-Borro', Name(first='Miguel', middle='', last='de Val-Borro')),
]


def test_cleaned_name():
    for original, cleaned in RAW_NAMES:
        assert _cleaned_name(original) == cleaned


def test_name_parsing():
    import probablepeople as pp
    from nameparser import HumanName

    for original, parsed in PARSED_NAMES:
        # It gets better results if you don't supply the 'type' parameter --
        # it gets Weir O'Phinney correct. So, use that, unless it guesses wrong
        # about the type, in which case, do it again using type=person.
        try:
            from_pp = pp.tag(_cleaned_name(original))
            if from_pp[1] != 'Person':
                from_pp = pp.tag(_cleaned_name(original), type='person')
            if from_pp[0].get('FirstInitial', ''):
                from_pp[0].update({'FirstName': from_pp.get('FirstInitial')})
            result = from_pp[0]
        except:
            from_hn = HumanName(_cleaned_name(original))
            result = {'GivenName': from_hn.first, 'Surname': from_hn.last}

        assert result.get('GivenName', '') == parsed.first
        assert result.get('Surname', '') == parsed.last



# def test_probablepeople():
#     from nameparser import HumanName
#     for original, parsed in PARSED_NAMES:
#         # It gets better results if you don't supply the 'type' parameter --
#         # it gets Weir O'Phinney correct. So, use that, unless it guesses wrong
#         # about the type, in which case, do it again using type=person.
#         from_hn = HumanName(_cleaned_name(original))
#         assert from_hn.first == parsed.first
#         assert from_hn.last == parsed.last
