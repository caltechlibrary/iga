import commonpy.exceptions
from functools import cache
import json
import os
import re
import base64
from sidetrack import log
from types import SimpleNamespace
import requests
from urllib.parse import quote, urlparse, urljoin

from iga.exceptions import GitHubError, InternalError
from iga.name_utils import split_name


class LazyEnvStr:
    def __init__(self, var_name):
        self.var_name = var_name
        self._value = None

    @property
    def value(self):
        if self._value is None:
            val = os.getenv(self.var_name, '')
            self._value = f'{val}/api/v4'
        return self._value

    def __str__(self):
        return self.value


API_URL = LazyEnvStr('GITLAB_URL')


class GitLabAPIError(Exception):
    pass


def _gitlab_get(endpoint, test_only=False):
    headers = {'Accept': 'application/json'}
    using_token = os.environ.get('GITLAB_TOKEN')
    if using_token:
        headers['Authorization'] = f'Bearer {using_token}'
    method = 'head' if test_only else 'get'
    try:
        if method == 'HEAD':
            response = requests.head(endpoint, headers=headers)
        else:
            response = requests.get(endpoint, headers=headers)

        if response.status_code == 401:
            raise GitLabAPIError(
                f'Unauthorized: Check your GitLab token or permissions. Endpoint: {endpoint}'
            )
        elif response.status_code == 429:
            # Too Many Requests error
            raise GitLabAPIError(
                f'Too Many Requests: Rate limit exceeded. Try again later. Endpoint: {endpoint}'
            )
        return response

    except requests.exceptions.RequestException as e:
        # Handle connection errors or timeouts
        raise GitLabAPIError(f'Request failed: {e}') from e


@cache
def _object_for_gitlab(api_url, cls):
    """Return object of class cls made from the data obtained from the API url."""
    try:
        response = _gitlab_get(api_url)
        if not response:
            return None
        log(f'unpacking JSON into object structure from {api_url}')

        # Create the desired object & add the api url in case it's needed later.
        obj = cls(response.json())
        obj.api_url = api_url
        return obj

    except GitLabAPIError as e:
        # Handle GitLab API specific errors
        log(f'GitLab API Error: {e}')
        raise InternalError('Encountered error trying to unpack GitLab data.') from e

    except Exception as ex:
        # Handle other unexpected errors
        log(f'Error: {ex}')
        raise InternalError(
            'Encountered unexpected error trying to unpack GitLab data.'
        ) from ex


class GitLabAccount(SimpleNamespace):
    """Simple data structure corresponding to a GitHub user or org account."""

    def __init__(self, user_dict):
        super().__init__(**user_dict)
        if os.environ.get('IGA_RUN_MODE') == 'debug':
            log('GitHub user data: ' + json.dumps(user_dict, indent=2))
        # Save the original data for debugging purposes.
        self._json_dict = user_dict


class GitLabAsset(SimpleNamespace):
    """Simple data structure corresponding to a GitHub file asset JSON object."""

    def __init__(self, asset_dict):
        super().__init__(**asset_dict)


class GitLabRelease(SimpleNamespace):
    """Simple data structure corresponding to a GitHub release JSON object."""

    def __init__(self, release_dict):
        super().__init__(**release_dict)
        if os.environ.get('IGA_RUN_MODE') == 'debug':
            log('GitHub release data: ' + json.dumps(release_dict, indent=2))
        if release_dict.get('owner', {}):
            self.author = GitLabAccount(release_dict['owner'])
        # Save the original data for debugging purposes.
        self._json_dict = release_dict


class GitLabRepo(SimpleNamespace):
    """Simple data structure corresponding to a GitHub repository JSON object.
    This object is enhanced with a "files" property that contains a list of
    the files in the default branch of the repository."""

    def __init__(self, repo_dict):
        super().__init__(**repo_dict)
        if os.environ.get('IGA_RUN_MODE') == 'debug':
            log('GitHub repo data: ' + json.dumps(repo_dict, indent=2))
        if repo_dict.get('owner', {}):
            self.author = GitLabAccount(repo_dict['owner'])
        # if repo_dict.get('organization'):
        #    self.organization = GitLabAccount(repo_dict['organization'])
        if repo_dict.get('license'):
            self.license = GitLabLicense(repo_dict['license'])
        # Save the original data for debugging purposes.
        self._json_dict = repo_dict


class GitLabLicense(SimpleNamespace):
    """Simple data structure corresponding to a license object."""

    def __init__(self, license_dict):
        super().__init__(**license_dict)


class GitLabFile(SimpleNamespace):
    """Simple data structure corresponding to a file in a repo."""

    def __init__(self, file_dict):
        super().__init__(**file_dict)


def gitlab_release(repo_name, tag, test_only=False):
    """Return a Release object corresponding to the tagged release in GitHub.

    If test_only is True, only check existence; don't create a Release object.
    """
    endpoint = f'{API_URL}/projects/{repo_name}/releases/{tag}'
    if test_only:
        log('testing for existence: ' + endpoint)
        return _gitlab_get(endpoint, test_only)

    log('getting GitLab release data from ' + endpoint)
    return _object_for_gitlab(endpoint, GitLabRelease)


def gitlab_repo(repo_name, test_only=False):
    """Return a Repo object corresponding to the named repo in GitLab."""
    endpoint = f'{API_URL}/projects/{repo_name}?license=true'
    if test_only:
        log('testing for existence: ' + endpoint)
        return _gitlab_get(endpoint, test_only)

    log('getting GitLab release data from ' + endpoint)
    return _object_for_gitlab(endpoint, GitLabRelease)


def gitlab_release_assets(repo_name, tag, all_assets):
    """Return a list of URLs for all the assets associated with the release."""

    release = gitlab_release(repo_name, tag)
    sources = release.assets['sources']
    assets = []
    for source in sources:
        if not all_assets:
            if source['format'] in ['zip']:
                assets.append(source['url'])
        else:
            log('option to get all assets is in effect')
            assets.append(source['url'])
    return assets


def gitlab_repo_filenames(repo, tag_name):
    """Return a list of filenames in the repo corresponding to the specified tag."""
    endpoint = f'{API_URL}/projects/{repo.id}/repository/tree'
    response = _gitlab_get(endpoint)
    if not response:
        log('got no tree or it does not exist')
        return ''
    files = [res['path'] for res in response.json()]
    return files


def gitlab_repo_file(repo, tag_name, filename):
    """Return the text contents of the named file in the repo object.

    The tag_name must be a release tag, and is used to find the version of
    the repository corresponding to that tag.
    """
    if filename in getattr(repo, '_files_contents', {}):
        log(f'{filename} found in the files of {repo}')
        return repo._files_contents[filename]

    endpoint = (
        f'{API_URL}/projects/{repo.id}/repository/files/{filename}?ref={tag_name}'
    )
    response = _gitlab_get(endpoint)
    if not response:
        log(f'got no content for file {filename} or it does not exist')
        return ''
    json_dict = response.json()
    if json_dict['encoding'] != 'base64':
        log(f'GitHub file encoding for {filename} is ' + json_dict['encoding'])
        raise InternalError('Unimplemented file encoding ' + json_dict['encoding'])

    contents = base64.b64decode(json_dict['content']).decode()
    if not getattr(repo, '_file_contents', {}):
        repo._file_contents = {}
    # Cache the file contents, so we don't have to get it from GitLab again.
    repo._file_contents[filename] = contents
    log(f'got contents for {filename} (length = {len(contents)} chars)')
    return contents


def gitlab_file_url(repo, filename, tag):
    """Return the URL of the named file in the repo."""
    endpoint = f'{API_URL}/projects/{repo.id}/repository/blobs/{filename}?ref={tag}'
    return endpoint


def gitlab_repo_languages(repo):
    log(f'asking GitHub for list of languages for repo {repo.name}')
    repolink = repo._links['self']
    endpoint = f'{repolink}/languages'
    response = _gitlab_get(endpoint)
    if not response:
        log(f'got no content for list of languages for repo {repo}')
        return ''
    json_dict = response.json()
    languages = json_dict.keys() if json_dict else []
    log(f'GitLab lists {len(languages)} languages for the repo')
    return languages


def gitlab_asset_contents(asset_url):
    """Return the raw contents of a release asset file."""
    try:
        response = _gitlab_get(asset_url)
        return response.content
    except KeyboardInterrupt:
        raise
    except commonpy.exceptions.CommonPyException:
        raise GitHubError(
            f'Failed to download GitHub asset at {asset_url}'
            ' – either it does not exist or it is inaccessible.'
        )
    except Exception:
        raise


def valid_gitlab_release_url(url):
    """Check if the provided URL is a valid GitLab release endpoint."""
    gitlab_api_pattern = r'^https?://[^/]+/api/v4/projects/[^/]+/releases/[^/]+$'
    gitlab_web_pattern = r'^https?://[^/]+/[^/]+/[^/]+/-/releases/[^/]+$'
    if not (re.match(gitlab_api_pattern, url) or re.match(gitlab_web_pattern, url)):
        log(f"URL does not match GitLab release URL pattern: {url}")
        return False
    return True


def gitlab_account_repo_tag(release_url):
    """{gitlab_projectid}/releases/{tag}"""
    parsed = urlparse(release_url)
    os.environ['GITLAB_URL'] = f'{parsed.scheme}://{parsed.netloc}'
    path = parsed.path
    path = path.rstrip('/')
    tag = path.split('/')[-1]
    y = '/'.join(path.split('/')[:-1])
    project_id = y.rstrip('-/releases').lstrip('/')
    project_id = quote(project_id, safe='')
    return (None, project_id, tag)


def gitlab_account(account_name):
    endpoint = f'{API_URL}/users?username={account_name}'  # without_project_bots=true
    try:
        response = _gitlab_get(endpoint)
        if not response:
            return None
        log(f'unpacking JSON into object structure from {endpoint}')

        # Create the desired object & add the api url in case it's needed later.
        jsn_response = response.json()
        obj = GitLabAccount(jsn_response[0])

        obj.api_url = endpoint
        return obj

    except GitLabAPIError as e:
        # Handle GitLab API specific errors
        log(f'GitLab API Error: {e}')
        raise InternalError('Encountered error trying to unpack GitLab data.') from e

    except Exception as ex:
        # Handle other unexpected errors
        log(f'Error: {ex}')
        raise InternalError(
            'Encountered unexpected error trying to unpack GitLab data.'
        ) from ex


def gitlab_repo_contributors(repo):
    repolink = repo._links['self']
    endpoint = f'{repolink}/repository/contributors'
    response = _gitlab_get(endpoint)
    if not response:
        log(f'got no content for list of contributors for repo {repo}')
        return []
    # The JSON data is a list containing a kind of minimal user info dict.
    contributors = []
    seen_names = set()
    for user_dict in response.json():
        new_contributor_name = user_dict['name']
        (given, family) = split_name(new_contributor_name)
        # this is done so that when a repo is imported from github to gitlab
        # it creates the same name but different order contributors. 
        sorted_names = tuple(sorted([family, given]))
        person_or_org = {'given_name': given, 'family_name': family, 'type': 'personal'}
        if sorted_names not in seen_names:
            seen_names.add(sorted_names)
            contributors.append({'person_or_org': person_or_org, 'role': {'id': 'other'}})
    log(f'repo has {len(contributors)} contributors')
    return contributors


def identity_from_gitlab(account, role=None):
    if account.name:
        (given, family) = split_name(account.name)
        person_or_org = {'given_name': given, 'family_name': family, 'type': 'personal'}
    else:
        # The GitHub account record has no name, and InvenioRDM won't pass
        # a record without a family name. All we have is the login name.
        person_or_org = {
            'given_name': '',
            'family_name': account.username,
            'type': 'personal',
        }
    result = {'person_or_org': person_or_org}
    return result

