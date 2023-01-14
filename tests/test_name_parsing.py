# =============================================================================
# @file    test_name_parsing.py
# @brief   Py.test cases for parts of record.py
# @created 2022-12-23
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/iga
# =============================================================================

from collections import namedtuple
from iga.record import _cleaned_name, _split_name

Name = namedtuple('Name', 'first last')

RAW_NAMES = [
    ('偏右', ''),
    ('王爵nice', 'nice'),
    ('勾三股四', ''),
    ('TZ | 天猪', 'TZ'),
    ('Mu-An ✌️ Chiou', 'Mu-An Chiou'),
]

PARSED_NAMES = [
    ('Mike Hucka', Name(first='Mike', last='Hucka')),
    ('Rafael França', Name(first='Rafael', last='França')),
    ('王爵nice', Name(first='', last='nice')),
    ('Wladimir J. van der Laan', Name(first='Wladimir J.', last='van der Laan')),
    ('Mu-An ✌️ Chiou', Name(first='Mu-An', last='Chiou')),
    ('PatrickJS [tipe.io]', Name(first='', last='PatrickJS')),
    ('Jose Diaz-Gonzalez', Name(first='Jose', last='Diaz-Gonzalez')),
    ('TJ Holowaychuk', Name(first='TJ', last='Holowaychuk')),
    ('Ian Storm Taylor', Name(first='Ian Storm', last='Taylor')),
    ('Dr Nic Williams', Name(first='Nic', last='Williams')),
    ("Matthew Weier O'Phinney", Name(first='Matthew', last="Weier O'Phinney")),
    ('TZ | 天猪', Name(first='', last='TZ')),
    ('Martin Luther King, Jr.', Name(first='Martin Luther', last='King')),
    ('Carla Rodriguez de García', Name(first='Carla', last='Rodriguez de García')),
    ('J. Robert Oppenheimer', Name(first='J. Robert', last='Oppenheimer')),
    ('Jean-Jacques Rousseau', Name(first='Jean-Jacques', last='Rousseau')),
    ('Miguel de Cervantes', Name(first='Miguel', last='de Cervantes')),
    ("Weir O'Phinney", Name(first='Weir', last="O'Phinney")),
    ('Iuri de Silvio', Name(first='Iuri', last='de Silvio')),
    ('Miguel de Val-Borro', Name(first='Miguel', last='de Val-Borro')),
]


def test_cleaned_name():
    for original, cleaned in RAW_NAMES:
        assert _cleaned_name(original) == cleaned


def test_name_parsing():
    for original, parsed in PARSED_NAMES:
        (first, last) = _split_name(original)
        assert first == parsed.first
        assert last == parsed.last
