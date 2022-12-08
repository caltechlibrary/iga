# =============================================================================
# @file    test_init.py
# @brief   Py.test cases for module __init__.py file
# @created 2022-12-08
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/iga
# =============================================================================

def test_version():
    """Test version import."""
    from iga import __version__
    assert __version__


def test_print_version(capsys):
    from iga import print_version
    print_version()
    captured = capsys.readouterr()
    assert 'URL' in captured.out
