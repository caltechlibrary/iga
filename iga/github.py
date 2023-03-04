'''
github.py: IGA module for interacting with GitHub

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2022 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

from   commonpy.network_utils import net
import json
import os
from   sidetrack import log
from   types import SimpleNamespace

from iga.exceptions import GitHubError, InternalError


# Classes.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class GitHubRelease(SimpleNamespace):
    '''Simple data structure corresponding to a GitHub release JSON object.'''
    def __init__(self, release_dict):
        super().__init__(**release_dict)
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
        self.owner = GitHubAccount(repo_dict['owner'])
        log('GitHub repo data: ' + json.dumps(repo_dict, indent=2))
        if repo_dict.get('organization', None):
            self.organization = GitHubAccount(repo_dict['organization'])
        if repo_dict.get('license', None):
            self.license = GitHubLicense(repo_dict['license'])
        # Save the original data for debugging purposes.
        self._json_dict = repo_dict


class GitHubAccount(SimpleNamespace):
    '''Simple data structure corresponding to a GitHub user or org account.'''
    def __init__(self, user_dict):
        super().__init__(**user_dict)
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


# Principal exported functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def github_release(account_name, repo_name, tag_name):
    '''Return a Release object corresponding to the tagged release in GitHub.'''
    endpoint = ('https://api.github.com/repos/' + account_name
                + '/' + repo_name + '/releases/tags/' + tag_name)
    log('getting GitHub data for release at ' + endpoint)
    return _object_for_github(endpoint, GitHubRelease)


def github_account(account_name):
    '''Return an Account object corresponding to the GitHub user account.'''
    endpoint = 'https://api.github.com/users/' + account_name
    log('getting GitHub data for user at ' + endpoint)
    return _object_for_github(endpoint, GitHubAccount)


def github_repo(account_name, repo_name):
    '''Return a Repo object corresponding to the named repo in GitHub.'''
    endpoint = 'https://api.github.com/repos/' + account_name + '/' + repo_name
    log('getting GitHub data for repo at ' + endpoint)
    return _object_for_github(endpoint, GitHubRepo)


def github_repo_filenames(repo):
    '''Return a list of file information objects for the given repo object.'''
    if getattr(repo, '_filenames', None):
        return repo._filenames
    log('asking GitHub for list of files at ' + repo.api_url)
    files_url = repo.api_url + '/git/trees/' + repo.default_branch
    response = _github_get(files_url)
    if not response:
        log(f'did not get a list of file names for {repo}')
        return []
    json_dict = json.loads(response.text)
    files = [GitHubFile(data) for data in json_dict['tree']]
    log(f'found {len(files)} files in repo')
    # Cache the results on the repo object, so we don't have to recompute it.
    repo._files = files
    repo._filenames = [file.path for file in files]
    return repo._filenames


def github_repo_file(repo, filename):
    '''Return the text contents of the named file in the repo object.'''
    if filename not in github_repo_filenames(repo):
        log(f'{filename} not found in the files of {repo}')
        return ''
    if filename in getattr(repo, '_files_contents', {}):
        log(f'{filename} found in the files of {repo}')
        return repo._files_contents[filename]
    log(f'get contents of file {filename} from GitHub repo {repo.full_name}')
    file = next(f for f in repo._files if f.path == filename)
    response = _github_get(file.url)
    if not response:
        log(f'got no content for file {filename} or it does not exist')
        return ''
    json_dict = json.loads(response.text)
    if json_dict['encoding'] != 'base64':
        log(f'GitHub file encoding for {filename} is ' + json_dict['encoding'])
        raise InternalError('Unimplemented file encoding ' + json_dict['encoding'])
    import base64
    contents = base64.b64decode(json_dict['content']).decode()
    if not getattr(repo, '_file_contents', {}):
        repo._file_contents = {}
    # Cache the file contents, so we don't have to get it from GitHub again.
    repo._file_contents[filename] = contents
    log(f'file {filename} content length is {len(contents)}')
    return contents


def github_repo_languages(repo):
    '''Return a list of languages used in the repo according to GitHub.'''
    log(f'asking GitHub for list of languages for repo {repo.full_name}')
    endpoint = repo.languages_url
    response = _github_get(endpoint)
    if not response:
        log(f'got no content for list of languages for repo {repo}')
        return ''
    json_dict = json.loads(response.text)
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
    for user_dict in json.loads(response.text):
        contributors.append(github_account(user_dict['login']))
    log(f'repo has {len(contributors)} contributors')
    return contributors


def github_account_repo_tag(release_url):
    '''Return tuple (account, repo name, tag) based on the given web URL.'''
    # Example URL: https://github.com/mhucka/taupe/releases/tag/v1.2.0
    # Note this is not the same as the "release url" below.
    _, _, _, account, repo, _, _, tag = release_url.split('/')
    return (account, repo, tag)


def github_file_url(repo, filename):
    '''Return a URL that can be used to download the given file from the repo.'''
    return repo.html_url + '/blob/' + repo.default_branch + '/' + filename


def valid_github_release_url(release_url):
    '''Return True if the given URL appears to be a valid GitHub release URL.'''
    split_url = release_url.split('/')
    return (release_url.startswith('https://github.com')
            and len(split_url) == 8
            and split_url[5] == 'releases'
            and split_url[6] == 'tag')


# Helper functions
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def _object_for_github(api_url, cls):
    '''Return object of class cls made from the data obtained from the API url.'''
    response = _github_get(api_url)
    if not response:
        return None
    log(f'unpacking JSON into object structure from {api_url}')
    try:
        # Create the desired object & add the api url in case it's needed later.
        obj = cls(json.loads(response.text))
        obj.api_url = api_url
        return obj
    except Exception as ex:
        # Something unexpected happened. We need to fix our handling.
        log('Error: ' + str(ex))
        raise InternalError('Encountered error trying to get GitHub data.')


def _github_get(endpoint):
    headers = {'Accept': 'application/vnd.github.v3+json'}
    using_token = 'GITHUB_TOKEN' in os.environ
    if using_token:
        headers['Authorization'] = f'token {os.environ["GITHUB_TOKEN"]}'
    response, error = net('get', endpoint, headers=headers)
    if error:
        import commonpy.exceptions
        if isinstance(error, commonpy.exceptions.NoContent):
            # The requested thing does not exist.
            log(f'got no content for {endpoint}')
            return None
        elif isinstance(error, commonpy.exceptions.AuthenticationFailure):
            # GitHub is unusual in returning 403 when you hit the rate limit.
            # https://docs.github.com/en/rest/overview/resources-in-the-rest-api
            if 'API rate limit exceeded' in response.text:
                if using_token:
                    raise GitHubError('Rate limit exceeded – try again later')
                else:
                    raise GitHubError('Rate limit exceeded – try using a'
                                      ' personal access token, or wait some'
                                      ' time before trying again.')
            else:
                raise GitHubError('Permissions problem accessing ' + endpoint)
        elif isinstance(error, commonpy.exceptions.CommonPyException):
            raise GitHubError(error.args[0])
        else:
            raise error
    return response
