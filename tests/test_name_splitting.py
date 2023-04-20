# =============================================================================
# @file    test_name_splitting.py
# @brief   Py.test cases for parts of name_utils.py
# @created 2022-12-23
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/iga
# =============================================================================

from collections import namedtuple
from iga.name_utils import (
    split_name,
    is_person,
)

Name = namedtuple('Name', 'first last')

PARSED_NAMES = [
    ("Adam 'Atomic' Saltsman", Name(first='Adam', last='Saltsman')),
    ("Adán Miguel Sánchez Albert", Name(first='Adán Miguel Sánchez', last='Albert')),
    ("Ari", Name(first='', last='Ari')),
    ("Ching-Lan 'digdog' HUANG 黃 青嵐", Name(first='Ching-Lan', last='Huang')),
    ("Elijah Insua", Name(first='Elijah', last='Insua')),
    ("Francisco Ryan Tolmasky I", Name(first='Francisco Ryan', last='Tolmasky')),
    ("James Edward Gray II", Name(first='James Edward', last='Gray')),
    ("Jay Freeman (saurik)", Name(first='Jay', last='Freeman')),
    ("Jonathan 'Wolf' Rentzsch", Name(first='Jonathan', last='Rentzsch')),
    ("Kris Zyp", Name(first='Kris', last='Zyp')),
    ("Lim Chee Aun", Name(first='Lim Chee', last='Aun')),
    ("Matthew Weier O'Phinney", Name(first='Matthew', last="Weier O'Phinney")),
    ("Miguel de Icaza", Name(first='Miguel', last='de Icaza')),
    ("Miller Medeiros", Name(first='Miller', last='Medeiros')),
    ("Sam de Freyssinet", Name(first='Sam', last='de Freyssinet')),
    ('Andrey “A.I” Sitnik', Name(first='Andrey', last='Sitnik')),
    ('Ask Solem Hoel', Name(first='Ask Solem', last='Hoel')),
    ('Benjamin Arthur Lupton', Name(first='Benjamin Arthur', last='Lupton')),
    ('Carla Rodriguez de García', Name(first='Carla', last='Rodriguez de García')),
    ('Carlos Antonio da Silva', Name(first='Carlos Antonio', last='da Silva')),
    ('Christian Van Der Henst S.', Name(first='Christian', last='Van Der Henst S.')),
    ('Cristi Burcă', Name(first='Cristi', last='Burcă')),
    ('Dr Nic Williams', Name(first='Nic', last='Williams')),
    ('Fuji, Goro', Name(first='Fuji', last='Goro')),
    ('Georges Chreifi', Name(first='Georges', last='Chreifi')),
    ('Ian Storm Taylor', Name(first='Ian Storm', last='Taylor')),
    ('Irakli Gozalishvili', Name(first='Irakli', last='Gozalishvili')),
    ('Iuri de Silvio', Name(first='Iuri', last='de Silvio')),
    ('J. Robert Oppenheimer', Name(first='J. Robert', last='Oppenheimer')),
    ('Jasper Van der Jeugt', Name(first='Jasper', last='Van der Jeugt')),
    ('Jean-Jacques Rousseau', Name(first='Jean-Jacques', last='Rousseau')),
    ('Jose Diaz-Gonzalez', Name(first='Jose', last='Diaz-Gonzalez')),
    ('José Lorenzo Rodríguez', Name(first='José Lorenzo', last='Rodríguez')),
    ('Lukas Kahwe Smith', Name(first='Lukas Kahwe', last='Smith')),
    ('Martin Luther King, Jr.', Name(first='Martin Luther', last='King')),
    ('Miguel de Val-Borro', Name(first='Miguel', last='de Val-Borro')),
    ('Mike Hucka', Name(first='Mike', last='Hucka')),
    ('Mr.doob', Name(first='', last='Doob')),
    ('Mu-An ✌️ Chiou', Name(first='Mu-An', last='Chiou')),
    ('PatrickJS [tipe.io]', Name(first='', last='PatrickJS')),
    ('Philip (flip) Kromer', Name(first='Philip', last='Kromer')),
    ('R. Tyler Croy', Name(first='R. Tyler', last='Croy')),
    ('R.I.Pienaar', Name(first='R. I.', last='Pienaar')),
    ('Rafael França', Name(first='Rafael', last='França')),
    ('TJ Holowaychuk', Name(first='TJ', last='Holowaychuk')),
    ('TZ | 天猪', Name(first='', last='Tz')),
    ('Tokuhiro Matsuno', Name(first='Tokuhiro', last='Matsuno')),
    ('Weibin Yao(姚伟斌)', Name(first='Weibin', last='Yao')),
    ('Wladimir J. van der Laan', Name(first='Wladimir J.', last='van der Laan')),
    ('Yukihiro &quot;Matz&quot; Matsumoto', Name(first='Yukihiro', last='Matsumoto')),
    ('ara.t.howard', Name(first='Ara T.', last='Howard')),
    ('cho45', Name(first='', last='cho45')),
    ('王爵nice', Name(first='', last='Nice')),
    # ('', Name(first='', last='')),

    # Known failures:
    # ("SHIBATA Hiroshi", Name(first='Hiroshi', last='SHIBATA')),
]


def test_name_splitting():
    for original, parsed in PARSED_NAMES:
        (first, last) = split_name(original)
        assert first == parsed.first
        assert last == parsed.last
