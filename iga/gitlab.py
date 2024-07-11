import commonpy.exceptions
from   commonpy.network_utils import net
import contextlib
from   functools import cache
import json
import os
from   sidetrack import log
from   types import SimpleNamespace
import requests

from iga.exceptions import GitHubError, InternalError

_BOT_NAME_WORDS = ['daemon', 'dependabot', 'dependabot[bot]']
'''List of words such that, if one of the words is the last word in an account
name, mean the account will be assumed to be a software bot of some kind.'''

class GitLabAPIError(Exception):
    pass

def _gitlab_get(endpoint, test_only=False):
    headers = {'Accept': 'application/json'}
    using_token = 'GITLAB_TOKEN' in os.environ
    if using_token:
        headers['Authorization'] = f'token {os.environ["GITLAB_TOKEN"]}'
    method = 'head' if test_only else 'get'
    try:
        if method == 'HEAD':
            response = requests.head(endpoint, headers=headers)
        else:
            response = requests.get(endpoint, headers=headers)

        if response.status_code == 401:
            raise GitLabAPIError(f"Unauthorized: Check your GitLab token or permissions. Endpoint: {endpoint}")
        elif response.status_code == 429:
            # Too Many Requests error
            raise GitLabAPIError(f"Too Many Requests: Rate limit exceeded. Try again later. Endpoint: {endpoint}")
        return response

    except requests.exceptions.RequestException as e:
        # Handle connection errors or timeouts
        raise GitLabAPIError(f"Request failed: {e}") from e

@cache
def _object_for_gitlab(api_url, cls):
    '''Return object of class cls made from the data obtained from the API url.'''
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
        raise InternalError('Encountered unexpected error trying to unpack GitLab data.') from ex


class GitLabAccount(SimpleNamespace):
    '''Simple data structure corresponding to a GitHub user or org account.'''
    def __init__(self, user_dict):
        super().__init__(**user_dict)
        if os.environ.get('IGA_RUN_MODE') == 'debug':
            log('GitHub user data: ' + json.dumps(user_dict, indent=2))
        # Save the original data for debugging purposes.
        self._json_dict = user_dict

class GitLabAsset(SimpleNamespace):
    '''Simple data structure corresponding to a GitHub file asset JSON object.'''
    def __init__(self, asset_dict):
        super().__init__(**asset_dict)

class GitLabRelease(SimpleNamespace):
    '''Simple data structure corresponding to a GitHub release JSON object.'''
    def __init__(self, release_dict):
        super().__init__(**release_dict)
        if os.environ.get('IGA_RUN_MODE') == 'debug':
            log('GitHub release data: ' + json.dumps(release_dict, indent=2))
        self.author = GitLabAccount(release_dict['author'])

        # ... then convert the dict of the asset (which contains uploader).
        self.assets = [GitLabAsset(asset) for asset in self.assets]
        # Save the original data for debugging purposes.
        self._json_dict = release_dict



def gitlab_release(project_url, test_only=False):
    endpoint = project_url  # Assuming project_url points to the release endpoint
    if test_only:
        log('testing for existence: ' + endpoint)
        return _gitlab_get(endpoint, test_only)

    log('getting GitLab release data from ' + endpoint)
    return _object_for_gitlab(endpoint, GitLabRelease)

def gitlab_release_assets(project_url, get_all):
    '''Return a list of URLs for all the assets associated with the release.'''

    release = gitlab_release(project_url)
    sources = release.assets.sources
    assets = []
    for source in sources:
        if not get_all:
            if source.format in ['zip']:
                assets.append(source.url)
        else:
            log('option to get all assets is in effect')
            assets.append(source.url)
    return assets

def github_repo_file(repo, tag_name, filename):
    '''Return the text contents of the named file in the repo object.

    The tag_name must be a release tag, and is used to find the version of
    the repository corresponding to that tag.
    '''
    #https://code.jlab.org/api/v4/projects/31/repository/files/Pipfile/raw?ref=0.1.0


# /projects/:id/repository/files/:file_path