'''
github.py: IGA module for interacting with GitHub

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2022-2023 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

import commonpy.exceptions
from   commonpy.network_utils import network
from   functools import cache
import json
import os
from   sidetrack import log
from   types import SimpleNamespace

from iga.exceptions import GitHubError, InternalError


# Constants.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

_BASE_URL = 'https://api.github.com'
'''Base URL for GitHub's API endpoints.'''

# 2023-03-27 the following used to include "bot" (no brackets) in this list,
# but then I discovered a real person whose last name is "Bot"!

_BOT_NAME_WORDS = ['daemon', 'dependabot', 'dependabot[bot]']
'''List of words such that, if one of the words is the last word in an account
name, mean the account will be assumed to be a software bot of some kind.'''


# Classes.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class GitHubRelease(SimpleNamespace):
    '''Simple data structure corresponding to a GitHub release JSON object.'''
    def __init__(self, release_dict):
        super().__init__(**release_dict)
        if os.environ.get('IGA_RUN_MODE') == 'debug':
            log('GitHub release data: ' + json.dumps(release_dict, indent=2))
        self.author = GitHubAccount(release_dict['author'])
        # First, do in-place conversion of the 'uploader' field (a dict) ...
        for asset in self.assets:
            asset['uploader'] = GitHubAccount(asset['uploader'])
        # ... then convert the dict of the asset (which contains uploader).
        self.assets = [GitHubAsset(asset) for asset in self.assets]
        # Save the original data for debugging purposes.
        self._json_dict = release_dict


class GitHubRepo(SimpleNamespace):
    '''Simple data structure corresponding to a GitHub repository JSON object.
    This object is enhanced with a "files" property that contains a list of
    the files in the default branch of the repository.'''

    def __init__(self, repo_dict):
        super().__init__(**repo_dict)
        if os.environ.get('IGA_RUN_MODE') == 'debug':
            log('GitHub repo data: ' + json.dumps(repo_dict, indent=2))
        self.owner = GitHubAccount(repo_dict['owner'])
        if repo_dict.get('organization'):
            self.organization = GitHubAccount(repo_dict['organization'])
        if repo_dict.get('license'):
            self.license = GitHubLicense(repo_dict['license'])
        # Save the original data for debugging purposes.
        self._json_dict = repo_dict


class GitHubAccount(SimpleNamespace):
    '''Simple data structure corresponding to a GitHub user or org account.'''
    def __init__(self, user_dict):
        super().__init__(**user_dict)
        if os.environ.get('IGA_RUN_MODE') == 'debug':
            log('GitHub user data: ' + json.dumps(user_dict, indent=2))
        # Save the original data for debugging purposes.
        self._json_dict = user_dict


class GitHubAsset(SimpleNamespace):
    '''Simple data structure corresponding to a GitHub file asset JSON object.'''
    def __init__(self, asset_dict):
        super().__init__(**asset_dict)


class GitHubLicense(SimpleNamespace):
    '''Simple data structure corresponding to a license object.'''
    def __init__(self, license_dict):
        super().__init__(**license_dict)


class GitHubFile(SimpleNamespace):
    '''Simple data structure corresponding to a file in a repo.'''
    def __init__(self, file_dict):
        super().__init__(**file_dict)


# Exported module functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def github_release(account_name, repo_name, tag_name):
    '''Return a Release object corresponding to the tagged release in GitHub.'''
    endpoint = (_BASE_URL + '/repos/' + account_name + '/' + repo_name
                + '/releases/tags/' + tag_name)
    log('getting GitHub data for release at ' + endpoint)
    result = _object_for_github(endpoint, GitHubRelease)
    if not result:
        raise GitHubError(f'Can\'t get GitHub release data for {tag_name} in'
                          f' repository {repo_name} of account {account_name}')
    return result


def github_repo(account_name, repo_name):
    '''Return a Repo object corresponding to the named repo in GitHub.'''
    endpoint = _BASE_URL + '/repos/' + account_name + '/' + repo_name
    log('getting GitHub data for repo at ' + endpoint)
    result = _object_for_github(endpoint, GitHubRepo)
    if not result:
        raise GitHubError('Can\'t get GitHub repository data for'
                          f' {account_name}/{repo_name}')
    return result


def github_account(account_name):
    '''Return an Account object corresponding to the GitHub user account.'''
    endpoint = _BASE_URL + '/users/' + account_name
    log('getting GitHub data for user at ' + endpoint)
    result = _object_for_github(endpoint, GitHubAccount)
    if not result:
        raise GitHubError(f'Can\'t get GitHub account data for {account_name}')
    return result


def github_release_assets(account_name, repo_name, tag_name, get_all):
    '''Return a list of URLs for all the assets associated with the release.'''
    release = github_release(account_name, repo_name, tag_name)
    assets = [release.zipball_url]
    if get_all:
        log('option to get all assets is in effect')
        assets.append(release.tarball_url)
        for asset in release.assets:
            assets.append(asset.browser_download_url)

    log(f'found {len(assets)} assets for release "{tag_name}"')
    return assets


def github_asset_contents(asset_url):
    '''Return the raw contents of a release asset file.'''
    try:
        response = _github_get(asset_url)
        return response.content
    except KeyboardInterrupt:
        raise
    except commonpy.exceptions.CommonPyException:
        raise GitHubError(f'Failed to download GitHub asset at {asset_url}'
                          ' – either it does not exist or it is inaccessible.')
    except Exception:
        raise


def github_repo_filenames(repo, tag_name):
    '''Return a list of file information objects for the given repo object.

    The tag_name must be a release tag, and is used to find the version of
    the repository corresponding to that tag.
    '''
    if getattr(repo, '_filenames', None):
        return repo._filenames

    # We need to find the SHA for the file tree corresponding to the tag. There
    # is no direct API, so we have to start by getting info about all the tags.
    tags_endpoint = repo.api_url + '/git/refs/tags'
    response = _github_get(tags_endpoint)
    if not response:
        log(f'failed to get tags data using {tags_endpoint} – something is wrong')
        raise GitHubError('Unable to get list of tags for GitHub repository')

    # Next, we look up the specific commit by tag, then get the commit object.
    for tag_ref in response.json():     # The json in this case is a list.
        if tag_ref.get('ref', '').endswith(tag_name):
            tag_commit_url = tag_ref.get('object', {}).get('url', '')
            break
    else:
        log(f'failed to find tag {tag_name} in repo tag refs')
        return []
    response = _github_get(tag_commit_url)
    if not response:
        log(f'failed to get tag commit {tag_commit_url} – something is wrong')
        raise GitHubError(f'Unable to get needed GitHub data for release {tag_name}')

    # Next, we have to get the git commit object from that tag object. There
    # are two cases: one direct, and one with ane extra level of indirection.
    json_dict = response.json()
    if 'tree' not in json_dict:
        # We have to do one more lookup.
        git_commit_url = json_dict.get('object', {}).get('url', '')
        response = _github_get(git_commit_url)
        if not response:
            log(f'failed to get git commit {git_commit_url} – something is wrong')
            raise GitHubError(f'Unable to get needed GitHub data for release {tag_name}')
        json_dict = response.json()

    # Now we can finally get the file tree.
    tree_url = json_dict.get('tree', {}).get('url')
    response = _github_get(tree_url)
    if not response:
        log(f'failed to get file tree using {tree_url} – something is wrong')
        raise GitHubError('Unable to get list of files for GitHub repository')
    if not response:
        log(f'did not get a list of file names for {repo}')
        return []
    json_dict = response.json()
    files = [GitHubFile(data) for data in json_dict['tree']]
    log(f'GitHub returned a list of {len(files)} files in repo')
    # Cache the results on the repo object, so we don't have to recompute it.
    repo._files = files
    repo._filenames = [file.path for file in files]
    return repo._filenames


def github_repo_file(repo, tag_name, filename):
    '''Return the text contents of the named file in the repo object.

    The tag_name must be a release tag, and is used to find the version of
    the repository corresponding to that tag.
    '''
    if filename in getattr(repo, '_files_contents', {}):
        log(f'{filename} found in the files of {repo}')
        return repo._files_contents[filename]
    if filename not in github_repo_filenames(repo, tag_name):
        log(f'{filename} not found in the files of {repo}')
        return ''
    log(f'getting contents of file {filename} from GitHub repo {repo.full_name}')
    file = next(f for f in repo._files if f.path == filename)
    response = _github_get(file.url)
    if not response:
        log(f'got no content for file {filename} or it does not exist')
        return ''
    json_dict = response.json()
    if json_dict['encoding'] != 'base64':
        log(f'GitHub file encoding for {filename} is ' + json_dict['encoding'])
        raise InternalError('Unimplemented file encoding ' + json_dict['encoding'])
    import base64
    contents = base64.b64decode(json_dict['content']).decode()
    if not getattr(repo, '_file_contents', {}):
        repo._file_contents = {}
    # Cache the file contents, so we don't have to get it from GitHub again.
    repo._file_contents[filename] = contents
    log(f'got contents for {filename} (length = {len(contents)} chars)')
    return contents


def github_repo_languages(repo):
    '''Return a list of languages used in the repo according to GitHub.'''
    log(f'asking GitHub for list of languages for repo {repo.full_name}')
    endpoint = repo.languages_url
    response = _github_get(endpoint)
    if not response:
        log(f'got no content for list of languages for repo {repo}')
        return ''
    json_dict = response.json()
    languages = json_dict.keys() if json_dict else []
    log(f'GitHub lists {len(languages)} languages for the repo')
    return languages


def github_repo_contributors(repo):
    '''Return a list of GitHubAccount objects for users shown as repo contributors.'''
    endpoint = repo.contributors_url
    log(f'asking GitHub for list of contributors for repo {repo.full_name}')
    response = _github_get(endpoint)
    if not response:
        log(f'got no content for list of contributors for repo {repo}')
        return []
    # The JSON data is a list containing a kind of minimal user info dict.
    contributors = []
    for user_dict in response.json():
        contributors.append(github_account(user_dict['login']))
    log(f'repo has {len(contributors)} contributors')
    return contributors


def github_account_repo_tag(release_url):
    '''Return tuple (account, repo name, tag) based on the given web URL.'''
    # Example URL: https://github.com/mhucka/taupe/releases/tag/v1.2.0
    # Note this is not the same as the "release url" below.
    _, _, _, account_name, repo_name, _, _, tag_name = release_url.split('/')
    return (account_name, repo_name, tag_name)


# FIXME
def github_file_url(repo, filename):
    '''Return a URL that can be used to download the given file from the repo.'''
    return repo.html_url + '/blob/' + repo.default_branch + '/' + filename


def valid_github_release_url(url):
    '''Return True if the given URL appears to be a valid GitHub release URL.'''
    split_url = url.split('/')
    return (len(split_url) == 8
            and split_url[0] in ['http:', 'https:']
            and split_url[2] in ['github.com', 'www.github.com']
            and split_url[5] == 'releases'
            and split_url[6] == 'tag')


def probable_bot(account):
    '''Return True if this account is probably a bot.

    Bot accounts on GitHub are supposed to have an explicit type value of "bot"
    but it turns out there are bots that don't have their account type set
    properly. This function tries to guess if an account is a bot based on
    its type and its name.
    '''
    if not account:
        return False
    # Beware that some user accounts have "None" for account.name.
    is_bot = (account.type == 'Bot'
              or account.login in _BOT_NAME_WORDS
              or (account.name
                  and account.name.lower().split()[-1] in _BOT_NAME_WORDS))
    log(f'account {account.login} looks like it {"is" if is_bot else "is NOT"} a bot')
    return is_bot


# Helper functions
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

@cache
def _object_for_github(api_url, cls):
    '''Return object of class cls made from the data obtained from the API url.'''
    response = _github_get(api_url)
    if not response:
        return None
    log(f'unpacking JSON into object structure from {api_url}')
    try:
        # Create the desired object & add the api url in case it's needed later.
        obj = cls(response.json())
        obj.api_url = api_url
        return obj
    except KeyboardInterrupt:
        raise
    except Exception as ex:
        # Something unexpected happened. We need to fix our handling.
        log('Error: ' + str(ex))
        raise InternalError('Encountered error trying to unpack GitHub data.')


def _github_get(endpoint):
    headers = {'Accept': 'application/vnd.github+json'}
    using_token = 'GITHUB_TOKEN' in os.environ
    if using_token:
        headers['Authorization'] = f'token {os.environ["GITHUB_TOKEN"]}'
    try:
        response = network('get', endpoint, headers=headers)
        return response                 # noqa PIE787
    except KeyboardInterrupt:
        raise
    except commonpy.exceptions.NoContent:
        log(f'got no content for {endpoint}')
    except commonpy.exceptions.AuthenticationFailure:
        # GitHub is unusual in returning 403 when you hit the rate limit.
        # https://docs.github.com/en/rest/overview/resources-in-the-rest-api
        if 'API rate limit exceeded' in response.text:
            if using_token:
                raise GitHubError('Rate limit exceeded – try again later')
            else:
                raise GitHubError('Rate limit exceeded – try to use a personal'
                                  ' access token, or wait and try again later.')
        else:
            raise GitHubError('Permissions problem accessing ' + endpoint)
    except commonpy.exceptions.CommonPyException as ex:
        raise GitHubError(ex.args[0]) from ex
    except Exception:
        raise
    return None
