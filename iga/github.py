'''
github.py: IGA module for interacting with GitHub

This file is part of https://github.com/caltechlibrary/iga/.

Copyright (c) 2022 by the California Institute of Technology.  This code
is open-source software released under a BSD-type license.  Please see the
file "LICENSE" for more information.
'''

from   commonpy.network_utils import net
import json5
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
        if repo_dict.get('organization', None):
            self.organization = GitHubAccount(**repo_dict['organization'])
        if repo_dict.get('license', None):
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


class GitHubUser(SimpleNamespace):
    '''Simple data structure corresponding to a user in GitHub.'''


# Principal exported functions.
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def github_release(release_url):
    '''Return a Release object corresponding to the tagged release in GitHub.'''
    log('getting GitHub data for release at ' + release_url)
    return object_for_github(release_url, GitHubRelease)


def github_user(account):
    '''Return a User object corresponding to the GitHub user account.'''
    user_url = 'https://api.github.com/users/' + account
    log('getting GitHub data for user at ' + user_url)
    return object_for_github(user_url, GitHubUser)


def github_repo(account, repo):
    '''Return a Repo object corresponding to the repo in GitHub.'''
    repo_url = 'https://api.github.com/repos/' + account + '/' + repo
    log('getting GitHub data for repo at ' + repo_url)
    return object_for_github(repo_url, GitHubRepo)


def github_repo_filenames(repo):
    '''Return a list of file information objects for the given repo.'''
    if getattr(repo, '_filenames', None):
        return repo._filenames
    log('asking GitHub for list of files at ' + repo.api_url)
    files_url = repo.api_url + '/git/trees/' + repo.default_branch
    (response, error) = net('get', files_url)
    if error:
        log('unable to get listof files for repo: ' + str(error))
        return []
    json_dict = json5.loads(response.text)
    files = [GitHubFile(**f) for f in json_dict['tree']]
    log(f'found {len(files)} files in repo')
    # Cache the results on the repo object, so we don't have to recompute it.
    repo._files = files
    repo._filenames = [file.path for file in files]
    return repo._filenames


def github_repo_file(repo, filename):
    '''Return the text contents of the named file in the repo.'''
    if filename not in github_repo_filenames(repo):
        return ''
    if filename in getattr(repo, '_files_contents', {}):
        return repo._files_contents[filename]
    file = next(f for f in repo._files if f.path == filename)
    (response, error) = net('get', file.url)
    if error:
        return ''
    file_dict = json5.loads(response.text)
    if file_dict['encoding'] != 'base64':
        log(f'GitHub file encoding for {filename} is ' + file_dict['encoding'])
        raise InternalError('Unimplemented file encoding ' + file_dict['encoding'])
    import base64
    contents = base64.b64decode(file_dict['content']).decode()
    if not getattr(repo, '_file_contents', {}):
        repo._file_contents = {}
    # Cache the file contents, so we don't have to get it from GitHub again.
    repo._file_contents[filename] = contents
    return contents
 

def github_account_repo_tag(release_web_url):
    '''Return tuple (account, repo name, tag) based on the given web URL.'''
    # Example URL: https://github.com/mhucka/taupe/releases/tag/v1.2.0
    # Note this is not the same as the "release url" below.
    _, _, _, account, repo, _, _, tag = release_web_url.split('/')
    return (account, repo, tag)


def github_release_url(account, repo, tag):
    return 'https://api.github.com/repos/'+account+'/'+repo+'/releases/tags/'+tag


def github_file_url(repo, filename):
    return repo.html_url + '/blob/' + repo.default_branch + '/' + filename


def valid_github_release_url(release_web_url):
    '''Return True if the given URL appears to be a valid GitHub release URL.'''
    split_url = release_web_url.split('/')
    return (release_web_url.startswith('https://github.com')
            and len(split_url) == 8
            and split_url[5] == 'releases'
            and split_url[6] == 'tag')


# Helper functions
# ~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

def object_for_github(api_url, cls):
    (response, error) = net('get', api_url)
    if error:
        import commonpy.exceptions
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
        obj = cls(json5.loads(response.text))
        obj.api_url = api_url
        return obj
    except Exception as ex:
        breakpoint()
        # GitHub returned an unexpected value. We need to fix our handling.
        log('unexpected problem decode json from GitHub: ' + str(ex))
        raise InternalError('GitHub returned an unexpected value.')
