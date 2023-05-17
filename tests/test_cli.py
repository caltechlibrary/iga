# =============================================================================
# @file    test_cli.py
# @brief   Py.test cases for module command-line interface
# @created 2022-12-08
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/iga
# =============================================================================

import click
import click.testing
import json5
import os
from   os import path
from   sidetrack import log
from   unittest.mock import patch

from   iga.exit_codes import ExitCode
from iga.github import (
    GitHubAccount,
    GitHubRelease,
    GitHubRepo,
)


# Mocks
# .............................................................................

here      = path.dirname(path.abspath(__file__))
repo_dir  = path.join(here, 'data/fake-example/')
orcid_dir = path.join(here, 'data/orcid-examples/')


def mocked_invenio_api_available(server_url):
    return True


def mocked_invenio_token_valid(server_url):
    return True


def mocked_invenio_server_name(server_url):
    return 'TestServer'


def mocked_github_account(account_name):
    log(f'returing mocked GitHubAccount for {account_name}')
    with open(path.join(repo_dir, 'account.json'), 'r') as f:
        return GitHubAccount(json5.loads(f.read()))


def mocked_github_repo(account_name, repo_name):
    log(f'returing mocked GitHubRepo for {repo_name}')
    with open(path.join(repo_dir, 'repo.json'), 'r') as f:
        repo = GitHubRepo(json5.loads(f.read()))
        repo._files = mocked_github_repo_filenames(repo_name, 'faketag')
        return repo


def mocked_github_release(account_name, repo_name, tag_name):
    log(f'returing mocked GitHubRelease for {tag_name}')
    with open(path.join(repo_dir, 'release.json'), 'r') as f:
        return GitHubRelease(json5.loads(f.read()))


def mocked_github_repo_filenames(repo, tag_name):
    log('returing mocked filenames list')
    with open(path.join(repo_dir, 'filenames.json'), 'r') as f:
        return json5.loads(f.read())


def mocked_github_repo_file(repo, tag_name, filename):
    log(f'returing mocked file contents for {filename}')
    with open(path.join(repo_dir, filename), 'r') as f:
        return f.read()


def mocked_github_repo_contributors(repo):
    log('returing mocked contributors')
    return []


def mocked_github_repo_languages(repo):
    log('returing mocked languages')
    return ['fakelanguage1', 'fakelanguage2']


def mocked_orcid_data(orcid):
    log(f'returing mocked orcid data for {orcid}')
    orcid_filename = orcid + '.json'
    with open(path.join(orcid_dir, orcid_filename), 'r') as f:
        return json5.load(f)


# Tests
# .............................................................................

@patch.dict(os.environ, {}, clear=True)
@patch('iga.invenio.invenio_api_available', new=mocked_invenio_api_available)
@patch('iga.invenio.invenio_token_valid', new=mocked_invenio_token_valid)
@patch('iga.invenio.invenio_server_name', new=mocked_invenio_server_name)
@patch('iga.github.github_repo_file', new=mocked_github_repo_file)
@patch('iga.github.github_repo_filenames', new=mocked_github_repo_filenames)
@patch('iga.github.github_repo_languages', new=mocked_github_repo_languages)
@patch('iga.github.github_repo_contributors', new=mocked_github_repo_contributors)
@patch('iga.github.github_account', new=mocked_github_account)
@patch('iga.github.github_repo', new=mocked_github_repo)
@patch('iga.github.github_release', new=mocked_github_release)
@patch('iga.orcid.orcid_data', new=mocked_orcid_data)
def test_environment_vars_from_options(capsys):
    from iga.cli import cli
    runner = click.testing.CliRunner()
    args = ['--invenio-server', 'https://data.caltechlibrary.dev',
            '--invenio-token', 'itoken',
            '--github-token', 'gtoken',
            '--save-metadata', '/tmp/fake.json',
            'https://github.com/fakeaccount/fakerepo/releases/tag/fakerelease']
    result = runner.invoke(cli, args)
    assert result.exit_code == int(ExitCode.success)
    assert 'INVENIO_SERVER' in os.environ
    assert os.environ['INVENIO_SERVER'] == 'https://data.caltechlibrary.dev'
    assert 'INVENIO_TOKEN' in os.environ
    assert os.environ['INVENIO_TOKEN'] == 'itoken'
    assert 'GITHUB_TOKEN' in os.environ
    assert os.environ['GITHUB_TOKEN'] == 'gtoken'


def test_no_args(capsys):
    from iga.cli import cli
    runner = click.testing.CliRunner()
    result = runner.invoke(cli)
    assert 'Usage' in result.output
    assert result.exit_code == int(ExitCode.success)


def test_unknown_arg(capsys):
    from iga.cli import cli
    runner = click.testing.CliRunner()
    result = runner.invoke(cli, ['--foo'])
    assert 'No such option' in result.output
    assert result.exit_code == int(ExitCode.bad_arg)


def test_help_flag(capsys):
    from iga.cli import cli
    runner = click.testing.CliRunner()
    result = runner.invoke(cli, ['--help'])
    assert 'Usage' in result.output
    assert result.exit_code == int(ExitCode.success)
    result = runner.invoke(cli, ['-h'])
    assert 'Usage' in result.output
    assert result.exit_code == int(ExitCode.success)


# Currently broken.
# def test_help_arg(monkeypatch):
#     from iga.cli import cli
#     runner = click.testing.CliRunner()
#     result = runner.invoke(cli, ['help'])
#     assert result.exit_code == int(ExitCode.success)


def test_mode(capsys):
    from iga.cli import cli
    runner = click.testing.CliRunner()
    result = runner.invoke(cli, ['--mode'])
    assert 'requires an argument' in result.output
    assert result.exit_code == int(ExitCode.bad_arg)


def test_version(capsys):
    from iga.cli import cli
    runner = click.testing.CliRunner()
    result = runner.invoke(cli, ['--version'])
    assert 'version' in result.output
    assert result.exit_code == int(ExitCode.success)


def test_incomplete_file_arg(capsys):
    from iga.cli import cli
    runner = click.testing.CliRunner()
    result = runner.invoke(cli, ['-f'])
    assert 'requires an argument' in result.output
    assert result.exit_code == int(ExitCode.bad_arg)
