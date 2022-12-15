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
from iga.exceptions import ReleaseError, GitHubError, InternalError


class Release(SimpleNamespace):
    def __init__(self, release_dict):
        super().__init__(**release_dict)
        self.author = SimpleNamespace(**release_dict['author'])
        # First do in-place conversion of the uploader field (a dict), then do
        # convert the dict of the containing asset.
        for asset in self.assets:
            asset['uploader'] = SimpleNamespace(**asset['uploader'])
        self.assets = [SimpleNamespace(**asset) for asset in self.assets]


def well_formed(release_url):
    return (release_url.startswith('https://github.com')
            and '/releases/tag/' in release_url)


def owner_repo_tag(release_url):
    # Example URL: https://github.com/mhucka/taupe/releases/tag/v1.2.0
    _, _, owner, repo, _, _, tag = release_url.replace('/', ' ').split()
    return (owner, repo, tag)


def github_release(release_url):
    if not well_formed(release_url):
        log('release_url not well-formed: ' + str(release_url))
        raise ReleaseError('Malformed release URL: ' + str(release_url))

    owner, repo, tag = owner_repo_tag(release_url)
    url = 'https://api.github.com/repos/'+owner+'/'+repo+'/releases/tags/'+tag
    (response, error) = net('get', url)
    if error:
        log('error from GitHub: ' + str(error))
        raise GitHubError(str(error))
    return Release(json.loads(response.text))
