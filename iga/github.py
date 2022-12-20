'''
github.py: IGA module for interacting with GitHub

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2022 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

from   commonpy.network_utils import net
import json
from   sidetrack import log
from   types import SimpleNamespace

from iga.exceptions import GitHubError, InternalError


# Classes.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

class GitHubRelease(SimpleNamespace):
    '''Simple data structure corresponding to a GitHub release JSON object.'''
    def __init__(self, release_dict):
        super().__init__(**release_dict)
        self.author = GitHubAccount(**release_dict['author'])
        # First, do in-place conversion of the 'uploader' field (a dict) ...
        for asset in self.assets:
            asset['uploader'] = GitHubAccount(**asset['uploader'])
        # ... then convert the dict of the asset (which contains uploader).
        self.assets = [GitHubAsset(**asset) for asset in self.assets]
        # Save the original data for debugging purposes.
        self._json_dict = release_dict


class GitHubRepo(SimpleNamespace):
    '''Simple data structure corresponding to a GitHub repository JSON object.
    This object is enhanced with a "files" property that contains a list of
    the files in the default branch of the repository.'''

    def __init__(self, repo_dict):
        super().__init__(**repo_dict)
        self.owner = GitHubAccount(**repo_dict['owner'])
        if 'organization' in repo_dict:
            self.organization = GitHubAccount(**repo_dict['organization'])
        if 'license' in repo_dict:
            self.license = GitHubLicense(**repo_dict['license'])
        # Save the original data for debugging purposes.
        self._json_dict = repo_dict


class GitHubAccount(SimpleNamespace):
    '''Simple data structure corresponding to a GitHub account JSON object.'''


class GitHubAsset(SimpleNamespace):
    '''Simple data structure corresponding to a GitHub file asset JSON object.'''


class GitHubLicense(SimpleNamespace):
    '''Simple data structure corresponding to a license object.'''


class GitHubFile(SimpleNamespace):
    '''Simple data structure corresponding to a file in a repo.'''


# Principal exported functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def github_release(release_url):
    '''Return a Release object corresponding to the tagged release in GitHub.'''
    log('getting GitHub data for release at ' + release_url)
    return object_for_github(release_url, GitHubRelease)


def github_repo(account, repo):
    '''Return a Repo object corresponding to the repo in GitHub.'''
    repo_url = 'https://api.github.com/repos/' + account + '/' + repo
    log('getting GitHub data for repo at ' + repo_url)
    return object_for_github(repo_url, GitHubRepo)


def github_repo_files(repo):
    '''Return a list of file information objects for the given repo.'''
    log('asking GitHub for list of files at ' + repo.api_url)
    files_url = repo.api_url + '/git/trees/' + repo.default_branch
    (response, error) = net('get', files_url)
    if error:
        log('unable to get listof files for repo: ' + str(error))
        return []
    json_dict = json.loads(response.text)
    log(f'found {len(json_dict["tree"])} files in repo')
    return [GitHubFile(**f) for f in json_dict['tree']]


def valid_github_release_url(release_web_url):
    '''Return True if the given URL appears to be a valid GitHub release URL.'''
    split_url = release_web_url.split('/')
    return (release_web_url.startswith('https://github.com')
            and len(split_url) == 8
            and split_url[5] == 'releases'
            and split_url[6] == 'tag')


def github_account_repo_tag(release_web_url):
    '''Return tuple (account, repo name, tag) based on the given release URL.'''
    # Example URL: https://github.com/mhucka/taupe/releases/tag/v1.2.0
    _, _, _, account, repo, _, _, tag = release_web_url.split('/')
    return (account, repo, tag)


# Helper functions
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def object_for_github(api_url, cls):
    (response, error) = net('get', api_url)
    if error:
        import commonpy
        if isinstance(error, commonpy.exceptions.AuthenticationFailure):
            # GitHub returns 403 when you hit the rate limit.
            # https://docs.github.com/en/rest/overview/resources-in-the-rest-api
            if 'API rate limit exceeded' in response.text:
                raise GitHubError('Exceeded rate limit -- try again later')
            else:
                raise GitHubError('Permissions problem accessing ' + api_url)
        elif isinstance(error, commonpy.exceptions.RateLimitExceeded):
            raise GitHubError('Exceeded rate limit -- try again later')
        elif isinstance(error, commonpy.exceptions.CommonPyException):
            raise GitHubError(error.args[0])
        else:
            raise error
    log('unpacking JSON into object structure')
    try:
        # Create the desired object & add the api url in case it's needed later.
        obj = cls(json.loads(response.text))
        obj.api_url = api_url
        return obj
    except json.decoder.JSONDecodeError as ex:
        # GitHub returned an unexpected value. We need to fix our handling.
        log('unexpected problem decode json from GitHub: ' + str(ex))
        raise InternalError('GitHub returned an unexpected value.')
