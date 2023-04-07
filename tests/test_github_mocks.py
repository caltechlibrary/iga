import iga.github
from iga.github import GitHubRelease, GitHubRepo, GitHubAccount
from os import path
import json5
from unittest.mock import patch

HERE = path.dirname(path.abspath(__file__))


def test_mocking_release(mocker):
    release_file = path.join(HERE, 'data', 'github-examples', 'with-codemeta',
                             'cds-astro', 'tutorials', 'release.json')
    with open(release_file, 'r') as f:
        release_json = json5.load(f)

    mocked_function = mocker.patch("iga.github._object_for_github")
    mocked_function.return_value = GitHubRelease(release_json)
    value = mocked_function()
    assert isinstance(value, GitHubRelease)
    assert value.id == 89397362
    assert value.author.login == 'ManonMarchand'


def test_mocking_repo(mocker):
    repo_file = path.join(HERE, 'data', 'github-examples', 'with-codemeta',
                          'cds-astro', 'tutorials', 'repo.json')
    with open(repo_file, 'r') as f:
        repo_json = json5.load(f)

    mocked_function = mocker.patch("iga.github._object_for_github")
    mocked_function.return_value = GitHubRepo(repo_json)
    value = mocked_function()
    assert isinstance(value, GitHubRepo)
    assert value.name == 'tutorials'
    assert value.owner.login == 'cds-astro'
    assert value.subscribers_count == 10


def test_mocking_account(mocker):
    account_file = path.join(HERE, 'data', 'github-examples', 'with-codemeta',
                             'datacite', 'akita', 'account.json')
    with open(account_file, 'r') as f:
        account_json = json5.load(f)

    mocked_function = mocker.patch("iga.github._object_for_github")
    mocked_function.return_value = GitHubAccount(account_json)
    value = mocked_function()
    assert isinstance(value, GitHubAccount)
    assert value.url == 'https://api.github.com/users/datacite'


def test_mocking_repo_file(mocker):
    codemeta_file = path.join(HERE, 'data', 'github-examples', 'with-codemeta',
                              'cds-astro', 'tutorials', 'codemeta.json')
    with open(codemeta_file, 'r') as f:
        codemeta_json = json5.load(f)

    mocked_function = mocker.patch("iga.github.github_repo_file")
    mocked_function.return_value = codemeta_json
    value = mocked_function('foo/repo', 'codemeta.json')
    assert isinstance(value, dict)
    assert value['codeRepository'] == 'git+https://github.com/cds-astro/tutorials'


@patch('iga.github.github_release', autospec=True, return_value = 'biff')
def test_patch_github_release(*args):
    assert iga.github.github_release('a', 'b', 'c') == 'biff'


@patch('iga.github.github_repo', autospec=True, return_value = 'bar')
def test_patch_github_repo(*args):
    assert iga.github.github_repo('a', 'b') == 'bar'


@patch('iga.github.github_release', autospec=True, return_value = 'biff')
@patch('iga.github.github_repo', autospec=True, return_value = 'bar')
def test_patch_all(*args):
    assert iga.github.github_repo('a', 'b') == 'bar'
    assert iga.github.github_release('a', 'b', 'c') == 'biff'
