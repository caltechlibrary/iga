from os import path
import pytest
from iga.gitlab  import (
    gitlab_account_repo_tag,
    valid_gitlab_release_url,

)

HERE = path.dirname(path.abspath(__file__))


def test_gitlab_account_repo_tag():
    url = 'https://gitlab.com/panta-123/test/-/releases/v0.0.1'
    assert gitlab_account_repo_tag(url) == (None, 'panta-123%2Ftest', 'v0.0.1')


@pytest.mark.parametrize("url, expected", [
    ("https://gitlab.com/panta-123/test/-/releases/v0.0.1", True),
    ("https://gitlab.com/username/repo/-/releases/v1.0.0", True),
    ("https://gitlab.com/api/v4/projects/username/repo/releases/", False),
    ("https://gitlab.com/username/repo/-/releases/", False),
    ("https://github.com/username/repo/releases/tag/v1.0.0", False),
    ("https://gitlab.com/username/repo/tree/master", False),
    ("https://gitlab.com/api/v4/projects/username/repo/issues", False),
    ("https://gitlab.com/username/repo/-/raw/master/README.md", False),
    ("https://gitlab.com", False),
    ("not_a_url", False),
])
def test_valid_gitlab_release_url(url, expected):
    assert valid_gitlab_release_url(url) == expected
