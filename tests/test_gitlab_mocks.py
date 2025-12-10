from os import path
import json5
from unittest.mock import patch, Mock
from pathlib import Path
import base64
import pytest

import iga.github
from iga.gitlab  import (
    GitLabAPIError,
    _gitlab_get,
    gitlab_release,
    gitlab_repo,
    gitlab_release_assets,
    gitlab_account_repo_tag,
    gitlab_repo_file,
    gitlab_account,
    GitLabRelease,
    GitLabRepo,
    GitLabAccount,
    GitLabAsset,
    GitLabLicense
)

import pytest
from pathlib import Path
import json5
from unittest.mock import Mock
from iga.gitlab import gitlab_release, gitlab_repo, gitlab_account, GitLabRelease, GitLabRepo, GitLabAccount

# Fixture for loading JSON data
@pytest.fixture
def load_json_data():
    def _load_json(file_name):
        file_path = Path(__file__).parent / 'data' / 'gitlab-examples' / file_name
        with file_path.open('r', encoding='utf-8') as f:
            return json5.load(f)
    return _load_json

# Fixture for mocking GitLab API responses
@pytest.fixture
def mock_gitlab_api(mocker):
    def _mock_api(json_data):
        mock_response = Mock()
        mock_response.json.return_value = json_data
        mocker.patch("iga.gitlab._gitlab_get", return_value=mock_response)
    return _mock_api

# Parameterized test for releases
@pytest.mark.parametrize("field", ["name", "description", "created_at", "tag_name", "released_at", "_links", "assets", "author"])
def test_gitlab_release(load_json_data, mock_gitlab_api, field):
    releases_json = load_json_data('release.json')
    mock_gitlab_api(releases_json)
    
    release = gitlab_release('61070808', "v0.0.1")
    assert getattr(release, field) == releases_json[field]

# Test for GitLab account
def test_gitlab_account(load_json_data, mock_gitlab_api):
    acc_json = load_json_data('account.json')[0]
    mock_gitlab_api([acc_json])
    
    acc = gitlab_account(acc_json['username'])
    assert acc.username == acc_json['username']
    assert acc.id == acc_json['id']

# Test for GitLab repo
@pytest.mark.parametrize("field", ["name", "id", "description", "created_at", "web_url", "updated_at", "license", "_links", "owner", "topics"])
def test_gitlab_repo(load_json_data, mock_gitlab_api, mocker, field):
    repo_json = load_json_data('repo.json')
    mock_gitlab_api(repo_json)
    repo = gitlab_repo('test')

    # Mock _object_for_gitlab to return a GitLabRepo instance
    mocked_function = mocker.patch("iga.gitlab._object_for_gitlab")
    mocked_function.return_value = GitLabRepo(repo_json)
    value = mocked_function()

    # Assert that both repo and value are instances of GitLabRepo
    assert isinstance(value, GitLabRepo)
    if field == "_links":
        assert repo._links["issues"] == repo_json['_links']["issues"]
        assert value._links["issues"] == repo_json['_links']["issues"]
    elif field == "license":
        assert repo.license == repo_json["license"]
        assert isinstance(value.license, GitLabLicense)
        assert value.license.name == repo_json["license"]["name"]
    else:
        assert getattr(repo, field) == repo_json[field]
        assert getattr(value, field) == repo_json[field]

@pytest.fixture
def mock_repo():
    repo = Mock(spec=GitLabRepo)
    repo.id = 12345
    repo._file_contents = {}
    return repo

def test_gitlab_repo_file(mock_repo, mocker):
    # Prepare the mock API response
    file_path = Path(__file__).parent / 'data' / 'gitlab-examples' / 'CITATION.cff'
    with file_path.open('r', encoding='utf-8') as f:
        mock_file_content = f.read()
    base64_content = base64.b64encode(mock_file_content.encode()).decode()
    
    mock_response = mocker.Mock()
    mock_response.json.return_value = {
        'content': base64_content,
        'encoding': 'base64',
    }

    # Patch the _gitlab_get function to return the mock response
    mock_gitlab_get = mocker.patch("iga.gitlab._gitlab_get", return_value=mock_response)

    # Call the function with the mock data
    filename = 'CITATION.cff'
    tag_name = 'v1.0'  # Example tag name
    content = gitlab_repo_file(mock_repo, tag_name, filename)

    # Assert the content matches what was read from the file
    assert content == mock_file_content

    # Assert the content is cached in the repo object
    assert mock_repo._file_contents[filename] == mock_file_content

    # Verify GitLab API interaction
    assert mock_repo.id == 12345  # Verify the mock repo ID
    mock_gitlab_get.assert_called_once()  # Verify API call

def test_gitlab_release_assets(load_json_data, mock_gitlab_api):
    # Setup
    releases_json = load_json_data('release.json')
    mock_gitlab_api(releases_json)

    # Exercise and Verify
    # Test with all_assets=False
    assets = gitlab_release_assets('61070808', "v0.0.1", all_assets=False)
    expected_assets = [
        source["url"] for source in releases_json['assets']['sources']
        if source["format"] == 'zip'
    ]
    assert assets == expected_assets

    # Test with all_assets=True
    assets = gitlab_release_assets('61070808', "v0.0.1", all_assets=True)
    expected_all_assets = [
        source["url"] for source in releases_json['assets']['sources']
    ]
    assert assets == expected_all_assets

    # Verify GitLabAsset instances
    for source in releases_json['assets']['sources']:
        asset = GitLabAsset(source)
        assert isinstance(asset, GitLabAsset)
        assert asset.url.startswith("https://gitlab.com/panta-123/test/-/archive/")

@pytest.mark.parametrize("mock_return", ['bar'])
def test_patch_gitlab_repo(mocker, mock_return):
    mocker.patch('iga.gitlab.gitlab_repo', return_value=mock_return)
    assert iga.gitlab.gitlab_repo('a', 'b') == mock_return
