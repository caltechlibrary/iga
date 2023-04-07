from os import path
import json5
from unittest.mock import patch

import iga.github
from iga.github import (
    GitHubRepo,
    github_account,
    github_account_repo_tag,
    github_file_url,
    valid_github_release_url)


def test_github_account():
    account = github_account('mhucka')
    assert account
    assert account.login == "mhucka"
    assert account.type == "User"

    try:
        account = github_account('55fake99zxy100')
    except iga.github.GitHubError:
        pass
    else:
        assert False


def test_github_account_repo_tag():
    url = 'https://github.com/foo/bar/releases/tag/v3.9.2'
    assert github_account_repo_tag(url) == ('foo', 'bar', 'v3.9.2')


def test_github_valid_release_url():
    assert valid_github_release_url('https://github.com/foo/bar/releases/tag/v3.9.2')
    assert not valid_github_release_url('https://github.com/foo/bar/releases/tag')


here = path.dirname(path.abspath(__file__))
json_file = 'data/github-examples/with-codemeta/fairdataihub/FAIRshare-Docs/repo.json'
with open(path.join(here, json_file), 'r') as f:
    repo_object = GitHubRepo(json5.loads(f.read()))

@patch('iga.github.github_repo', autospec=True, return_value = repo_object)
def test_repo_file_url(*args):
    repo = iga.github.github_repo('fairdataihub', 'FAIRshare-Docs')
    expected = 'https://github.com/fairdataihub/FAIRshare-Docs/blob/main/somefile'
    assert github_file_url(repo, 'somefile') == expected
