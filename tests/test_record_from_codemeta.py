import os
from os import path
import json5
from unittest.mock import patch

import iga.github
from iga.github import (
    GitHubRepo,
    GitHubRelease,
)


# Mocks
# .............................................................................

here         = path.dirname(path.abspath(__file__))
examples_dir = path.join(here, 'data/github-examples/with-codemeta')
repo_dir     = path.join(examples_dir, 'fairdataihub/FAIRshare-Docs')


def mocked_github_release(account, repo, tag):
    with open(path.join(repo_dir, 'release.json'), 'r') as f:
        return GitHubRelease(json5.loads(f.read()))


def mocked_github_repo(account, repo):
    with open(path.join(repo_dir, 'repo.json'), 'r') as f:
        return GitHubRepo(json5.loads(f.read()))


def mocked_github_repo_file(repo, filename):
    with open(path.join(repo_dir, filename), 'r') as f:
        return f.read()


def mocked_github_repo_filenames(repo):
    with open(path.join(repo_dir, 'filenames.json'), 'r') as f:
        return json5.loads(f.read())


# Tests
# .............................................................................

@patch('iga.github.github_release', new=mocked_github_release)
@patch('iga.github.github_repo', new=mocked_github_repo)
@patch('iga.github.github_repo_file', new=mocked_github_repo_file)
@patch('iga.github.github_repo_filenames', new=mocked_github_repo_filenames)
@patch.dict(os.environ, {'INVENIO_SERVER': 'data.caltechlibrary.dev',
                         'INVENIO_TOKEN': 'faketoken',
                         'GITHUB_TOKEN': 'faketoken'}, clear=True)
def test_repo_file_url(*args):
    from iga.metadata import metadata_for_release
    record = metadata_for_release('fairdataihub', 'FAIRshare-Docs', '4.2.19', False)
    expected_json = path.join(examples_dir, 'fairdataihub/FAIRshare-Docs-expected.json')
    with open(expected_json, 'r') as f:
        expected = json5.loads(f.read())
    assert record == expected
