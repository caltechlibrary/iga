# =============================================================================
# @file    test_text_utils.py
# @brief   Py.test cases for parts of text_utils.py
# @created 2023-03-02
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/iga
# =============================================================================

from typing import Generator
from iga.text_utils import (
    cleaned_text,
    without_html,
)


def test_cleaned_text():
    assert cleaned_text('') == ''
    assert cleaned_text('a  b') == 'a b'
    assert cleaned_text('a\nb') == 'a b'
    assert cleaned_text('a\t b') == 'a b'
    assert cleaned_text('some text.') == 'some text.'


def test_without_html():
    assert without_html('') == ''
    assert without_html('a') == 'a'
    assert without_html('this has no html') == 'this has no html'
    assert without_html('foo <i>bar</i>') == 'foo bar'
    assert without_html('Sjoberg, D., D., Whiting, K., Curry, M., Lavery, J., A., & Larmarange, J. (2021). Reproducible Summary Tables with the gtsummary Package. The R Journal, 13(1), 570. https://doi.org/10.32614/rj-2021-053\n') == 'Sjoberg, D., D., Whiting, K., Curry, M., Lavery, J., A., & Larmarange, J. (2021). Reproducible Summary Tables with the gtsummary Package. The R Journal, 13(1), 570. https://doi.org/10.32614/rj-2021-053'
