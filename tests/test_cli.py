# =============================================================================
# @file    test_cli.py
# @brief   Py.test cases for module command-line interface
# @created %CREATION_DATE%
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/%PROJECT_NAME%
# =============================================================================

import plac


def test_usage_help(capsys):
    from %PROJECT_NAME%.__main__ import main
    with plac.Interpreter(main) as i:
        i.check('-h', '')
