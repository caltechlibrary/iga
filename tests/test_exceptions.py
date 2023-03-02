# =============================================================================
# @file    test_exceptions.py
# @brief   Py.test cases for parts of exceptions.py
# @created 2023-03-02
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/iga
# =============================================================================

from iga.exceptions import IGAException, InternalError


def test_exceptions():
    try:
        raise InternalError('foo')
    except InternalError as ex:
        assert ex.args[0] == 'foo'

    try:
        raise InternalError('foo')
    except IGAException as ex:
        assert ex.args[0] == 'foo'
