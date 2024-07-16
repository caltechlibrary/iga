import rich_click as click
from   sidetrack import log
import os

from iga.github import (
    github_account_repo_tag,
    github_release,
    github_repo,
    github_release_assets,
    valid_github_release_url,
    github_repo_file,
    github_repo_filenames,
    github_repo_languages,
    github_asset_contents,
    github_account,
    github_repo_contributors
)
from iga.gitlab import (
    valid_gitlab_release_url,
    gitlab_release_assets,
    gitlab_repo,
    gitlab_repo_file,
    gitlab_release,
    gitlab_account_repo_tag,
    gitlab_repo_filenames,
    gitlab_repo_languages,
    gitlab_asset_contents,
    gitlab_account,
    gitlab_repo_contributors
)
try:
    if os.environ["GITLAB"]:
        GITLAB = True
except Exception as e:
    log(f"Error getting GitLab API URL: {e}")

GITLAB = True

def valid_release_url(release_url):
    if not GITLAB:
        return valid_github_release_url(release_url)
    else:
        return valid_gitlab_release_url(release_url)

def git_account_repo_tag(release_url):
    '''Return tuple (account, repo name, tag) based on the given web URL.'''
    # Example URL: https://code.jlab.org/physdiv/jrdb/inveniordm_jlab/-/releases/0.1.0
    # Note this is not the same as the "release url" below.
    if not GITLAB:
        return github_account_repo_tag(release_url)
    else:
        return gitlab_account_repo_tag(release_url)
    

def git_release(repo_name, tag, account_name=None):
    if not GITLAB:
        return github_release(account_name, repo_name, tag)
    else:
        return gitlab_release(repo_name, tag)

def git_repo(repo_name, account_name=None):
    if not GITLAB:
        return github_repo(account_name, repo_name)
    else:
        return gitlab_repo(repo_name)

def git_repo_filenames(repo, tag):
    if not GITLAB:
        return github_repo_filenames(repo, tag)
    else:
        return gitlab_repo_filenames(repo, tag)

def git_repo_file(repo, tag, filename):
    if not GITLAB:
        return github_repo_file(repo, tag, filename)
    else:
        print("here")
        return gitlab_repo_file(repo, tag, filename)
    
def git_release_assets(repo, tag, account_name=None, all_assets=False):
    if not GITLAB:
        return github_release_assets(account_name,repo, tag,  all_assets)
    else:
        return gitlab_release_assets(repo, tag, all_assets)

def git_account(repo):
    if not GITLAB:
        return github_account(repo)
    else:
        return gitlab_account(repo)

def git_repo_languages(repo):
    if not GITLAB:
        return github_repo_languages(repo)
    else:
        return gitlab_repo_languages(repo)

def git_asset_contents(asset):
    if not GITLAB:
        return github_asset_contents(asset)
    else:
        return gitlab_asset_contents(asset)
    
def git_repo_contributors(repo):
    if not GITLAB:
        return github_repo_contributors(repo)
    else:
        return gitlab_repo_contributors(repo)