# =============================================================================
# @file    test_name_utils.py
# @brief   Py.test cases for parts of name_utils.py
# @created 2023-03-02
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/iga
# =============================================================================

from iga.name_utils import (
    _cleaned_name,
    _plain_word,
    _upcase_first_letters,
    contains_cjk,
    flattened_name,
)

RAW_NAMES = [
    ('偏右', ''),
    ('王爵nice', 'nice'),
    ('勾三股四', ''),
    ('TZ | 天猪', 'TZ'),
    ('Mu-An ✌️ Chiou', 'Mu-An Chiou'),
]


def test_contains_cjk():
    assert contains_cjk('偏右')
    assert contains_cjk('王爵nice')
    assert not contains_cjk('test')
    assert not contains_cjk('éä')


def test_flattened_name():
    assert flattened_name('foo bar') == 'foo bar'
    assert flattened_name(['foo', 'bar']) == 'foo bar'
    assert flattened_name(['Foo J.', 'Bar']) == 'Foo J. Bar'
    assert flattened_name(['Foo', 'J.', 'Bar']) == 'Foo J. Bar'


def test_cleaned_name():
    for original, cleaned in RAW_NAMES:
        assert _cleaned_name(original) == cleaned


def test_plain_word():
    assert _plain_word('foo')
    assert _plain_word('FOO')
    assert _plain_word('Foo')
    assert not _plain_word('foo bar')
    assert not _plain_word('foo1')


def test_upcase_first_letter():
    assert _upcase_first_letters('aBC dEF') == 'ABC DEF'
    assert _upcase_first_letters('Abc Def') == 'Abc Def'
    assert _upcase_first_letters('abc def') == 'Abc Def'
    assert _upcase_first_letters('abc DEF') == 'Abc DEF'
    assert _upcase_first_letters('abc dEF') == 'Abc DEF'
    assert _upcase_first_letters('a') == 'A'
    assert _upcase_first_letters('A') == 'A'
