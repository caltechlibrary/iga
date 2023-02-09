# =============================================================================
# @file    test_name_parsing.py
# @brief   Py.test cases for parts of record.py
# @created 2022-12-23
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/iga
# =============================================================================

from collections import namedtuple
from iga.name_utils import _cleaned_name, split_name, flattened_name

Name = namedtuple('Name', 'first last')

RAW_NAMES = [
    ('偏右', ''),
    ('王爵nice', 'nice'),
    ('勾三股四', ''),
    ('TZ | 天猪', 'TZ'),
    ('Mu-An ✌️ Chiou', 'Mu-An Chiou'),
]

# Some of these names came from the following gist accessed on 2023-01-17:
# https://gist.github.com/paulmillr/2657075/a31455729440672467ada20ac10452d74a871e54

# Some real-life examples that we can't handle.
#
# * Ingy döt Net -- someone being cute, but it's not a real name
#
# * Rico Sta. Cruz -- "Sta. Cruz" is probably Santa Cruz, but neither PP nor
# nameparser figure it out and instead they think "Sta" is a middle name.
#
# These are businesses and I can't figure out what to do.  PP *could* tag them
# as company names, but PP also erroneously tags some human names as company,
# so the only way to avoid incorrectly tagging human names as companies is to
# *always* ignore PP's company tagging -- which means we always fail on these:
#
# * Account for Github research
# * Practical Arduino - The Book
# * Sony Xperia Developer World

PARSED_NAMES = [
    ('Mike Hucka', Name(first='Mike', last='Hucka')),
    ('Rafael França', Name(first='Rafael', last='França')),
    ('Wladimir J. van der Laan', Name(first='Wladimir J.', last='van der Laan')),
    ('Iuri de Silvio', Name(first='Iuri', last='de Silvio')),
    ('Ian Storm Taylor', Name(first='Ian Storm', last='Taylor')),
    ("Matthew Weier O'Phinney", Name(first='Matthew', last="Weier O'Phinney")),
    ('Martin Luther King, Jr.', Name(first='Martin Luther', last='King')),
    ('J. Robert Oppenheimer', Name(first='J. Robert', last='Oppenheimer')),
    ('Lukas Kahwe Smith', Name(first='Lukas Kahwe', last='Smith')),
    ('Philip (flip) Kromer', Name(first='Philip', last='Kromer')),
    ('Weibin Yao(姚伟斌)', Name(first='Weibin', last='Yao')),
    ('Dr Nic Williams', Name(first='Nic', last='Williams')),
    ('cho45', Name(first='', last='cho45')),
    ('王爵nice', Name(first='', last='Nice')),
    ('TZ | 天猪', Name(first='', last='Tz')),
    ('TJ Holowaychuk', Name(first='TJ', last='Holowaychuk')),
    ('PatrickJS [tipe.io]', Name(first='', last='PatrickJS')),
    ('Mu-An ✌️ Chiou', Name(first='Mu-An', last='Chiou')),
    ('Jean-Jacques Rousseau', Name(first='Jean-Jacques', last='Rousseau')),
    ('Jose Diaz-Gonzalez', Name(first='Jose', last='Diaz-Gonzalez')),
    ('Miguel de Val-Borro', Name(first='Miguel', last='de Val-Borro')),
    ('Carla Rodriguez de García', Name(first='Carla', last='Rodriguez de García')),
    ('R. Tyler Croy', Name(first='R. Tyler', last='Croy')),
    ('Mr.doob', Name(first='', last='Doob')),
    ('Yukihiro &quot;Matz&quot; Matsumoto', Name(first='Yukihiro', last='Matsumoto')),
    ("Adam 'Atomic' Saltsman", Name(first='Adam', last='Saltsman')),
    ('Andrey “A.I” Sitnik', Name(first='Andrey', last='Sitnik')),
    ("Ching-Lan 'digdog' HUANG 黃 青嵐", Name(first='Ching-Lan', last='Huang')),
    ('Fuji, Goro', Name(first='Fuji', last='Goro')),
    ('Christian Van Der Henst S.', Name(first='Christian', last='Van Der Henst S.')),
    ('R.I.Pienaar', Name(first='R. I.', last='Pienaar')),
    ('ara.t.howard', Name(first='Ara T.', last='Howard')),
    # ('', Name(first='', last='')),
]


def test_cleaned_name():
    for original, cleaned in RAW_NAMES:
        assert _cleaned_name(original) == cleaned


def test_name_parsing():
    for original, parsed in PARSED_NAMES:
        (first, last) = split_name(original)
        assert first == parsed.first
        assert last == parsed.last
