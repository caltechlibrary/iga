# =============================================================================
# @file    test_init.py
# @brief   Py.test cases for module __init__.py file
# @created %CREATION_DATE%
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/%PROJECT_NAME%
# =============================================================================

def test_version():
    """Test version import."""
    from %PROJECT_NAME% import __version__
    assert __version__


def test_print_version(capsys):
    from %PROJECT_NAME% import print_version
    print_version()
    captured = capsys.readouterr()
    assert 'URL' in captured.out
