# =============================================================================
# @file    test_licenses.py
# @brief   Py.test cases for parts of licenses.py
# @created 2023-03-02
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/iga
# =============================================================================

from iga.licenses import LICENSES, LICENSE_URLS


def test_licenses():
    assert len(LICENSES) > 100
    assert 'MIT' in LICENSES
    assert LICENSES['MIT'].title == 'MIT License'
    assert LICENSES['MIT'].url == 'https://spdx.org/licenses/MIT'


def test_license_urls():
    assert 'https://spdx.org/licenses/MIT' in LICENSE_URLS
    assert 'https://opensource.org/licenses/MIT' in LICENSE_URLS
    assert LICENSE_URLS['https://spdx.org/licenses/MIT'] == 'MIT'
    assert 'https://spdx.org/licenses/BSD-3-Clause' in LICENSE_URLS
