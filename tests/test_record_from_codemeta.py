# =============================================================================
# @file    test_record_from_codemeta.py
# @brief   Py.test cases for module metadata.py
# @created 2022-12-08
# @license Please see the file named LICENSE in the project directory
# @website https://github.com/caltechlibrary/iga
# =============================================================================

import os
from   os import path
import json5
from   sidetrack import log
from   unittest.mock import patch

import iga.github                       # noqa F401
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


def mocked_invenio_vocabulary(vocab):
    return [{'created': '2022-11-17T00:09:52.357057+00:00',
             'description': {'en': 'A permissive license.'},
             'icon': '',
             'id': 'apache-2.0',
             'links': {'self': 'https://data.caltechlibrary.dev/api/vocabularies/licenses/apache-2.0'},
             'props': {'osi_approved': 'y', 'scheme': 'spdx', 'url': 'http://www.apache.org/licenses/LICENSE-2.0'},
             'revision_id': 1,
             'tags': ['recommended', 'all', 'software'],
             'title': {'en': 'Apache License 2.0'},
             'type': 'licenses',
             'updated': '2022-11-17T00:09:52.368851+00:00'},
            {'created': '2022-11-17T00:09:52.356993+00:00',
             'description': {'en': ''},
             'icon': '',
             'id': 'bsd-3-clause',
             'links': {'self': 'https://data.caltechlibrary.dev/api/vocabularies/licenses/bsd-3-clause'},
             'props': {'osi_approved': 'y', 'scheme': 'spdx', 'url': 'https://opensource.org/licenses/BSD-3-Clause'},
             'revision_id': 1,
             'tags': ['all', 'software'],
             'title': {'en': 'BSD 3-Clause "New" or "Revised" License'},
             'type': 'licenses',
             'updated': '2022-11-17T00:09:52.366878+00:00'},
            {'created': '2022-11-17T00:09:52.419670+00:00',
             'description': {'en': 'A short and simple permissive license.'},
             'icon': '',
             'id': 'mit',
             'links': {'self': 'https://data.caltechlibrary.dev/api/vocabularies/licenses/mit'},
             'props': {'osi_approved': 'y', 'scheme': 'spdx', 'url': 'https://opensource.org/licenses/MIT'},
             'revision_id': 1,
             'tags': ['recommended', 'all', 'software'],
             'title': {'en': 'MIT License'},
             'type': 'licenses',
             'updated': '2022-11-17T00:09:52.430797+00:00'}]


def mocked_invenio_communities():
    return {}


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

@patch('iga.invenio.invenio_api_available', new=mocked_invenio_api_available)
@patch('iga.invenio.invenio_token_valid', new=mocked_invenio_token_valid)
@patch('iga.invenio.invenio_server_name', new=mocked_invenio_server_name)
@patch('iga.invenio.invenio_vocabulary', new=mocked_invenio_vocabulary)
@patch('iga.invenio.invenio_communities', new=mocked_invenio_communities)
@patch('iga.github.github_account', new=mocked_github_account)
@patch('iga.github.github_release', new=mocked_github_release)
@patch('iga.github.github_repo', new=mocked_github_repo)
@patch('iga.github.github_repo_file', new=mocked_github_repo_file)
@patch('iga.github.github_repo_filenames', new=mocked_github_repo_filenames)
@patch('iga.orcid.orcid_data', new=mocked_orcid_data)
@patch.dict(os.environ, {'INVENIO_SERVER': 'data.caltechlibrary.dev',
                         'INVENIO_TOKEN': 'faketoken',
                         'GITHUB_TOKEN': 'faketoken'}, clear=True)
def test_metadata(*args):
    from iga.metadata import metadata_for_release
    record = metadata_for_release('fakeaccount', 'fakerepo', 'fakerelease', False)
    expected_json = path.join(repo_dir, 'expected-metadata.json')
    with open(expected_json, 'r') as f:
        expected = json5.loads(f.read())
    assert record == expected
