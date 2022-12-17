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
import sys
from   types import SimpleNamespace

from iga.exit_codes import ExitCode
from iga.exceptions import GitHubError, InternalError


class GitHubRelease(SimpleNamespace):
    '''Simple data structure corresponding to GitHub release JSON data.'''
    def __init__(self, release_dict):
        super().__init__(**release_dict)
        self.author = GitHubAccount(**release_dict['author'])
        # First, do in-place conversion of the 'uploader' field (a dict) ...
        for asset in self.assets:
            asset['uploader'] = GitHubAccount(**asset['uploader'])
        # ... then convert the dict of the asset (which contains uploader).
        self.assets = [GitHubAsset(**asset) for asset in self.assets]


class GitHubAccount(SimpleNamespace):
    '''Simple data structure corresponding to GitHub account JSON objects.'''


class GitHubAsset(SimpleNamespace):
    '''Simple data structure corresponding to GitHub file asset JSON objects.'''


def github_release(release_url):
    log('getting GitHub data for release at ' + release_url)
    (response, error) = net('get', release_url)
    if error:
        import commonpy
        if isinstance(error, commonpy.exceptions.AuthenticationFailure):
            # GitHub returns 403 when you hit the rate limit.
            # https://docs.github.com/en/rest/overview/resources-in-the-rest-api
            if 'API rate limit exceeded' in response.text:
                raise GitHubError('Exceeded rate limit -- try again later')
            else:
                raise GitHubError('Permissions problem accessing ' + release_url)
        elif isinstance(error, commonpy.exceptions.RateLimitExceeded):
            raise GitHubError('Exceeded rate limit -- try again later')
        elif isinstance(error, commonpy.exceptions.CommonPyException):
            raise GitHubError(error.args[0])
        else:
            raise error
    log('unpacking JSON into object structure')
    try:
        return GitHubRelease(json.loads(response.text))
    except json.decoder.JSONDecodeError as ex:
        # GitHub returned an unexpected value. We need to fix our handling.
        log('unexpected problem decode json from GitHub: ' + str(ex))
        raise InternalError('GitHub returned an unexpected value.')
