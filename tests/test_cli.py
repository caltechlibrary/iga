# =============================================================================
# @file    test_cli.py
# @brief   Py.test cases for module command-line interface
# @created 2022-12-08
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/iga
# =============================================================================

import plac


def test_usage_help(capsys):
    from iga.__main__ import main
    with plac.Interpreter(main) as i:
        i.check('-h', '')
