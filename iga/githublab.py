import rich_click as click

from iga.github import (
    github_account_repo_tag,
    github_release,
    github_repo,
    github_release_assets,
    valid_github_release_url,
    github_repo_file,
)
from iga.gitlab import (
    valid_gitlab_release_url,
    gitlab_release_assets,
    gitlab_repo,
    gitlab_repo_file,
    gitlab_release,
)
ctx = click.get_current_context()
GITLAB = ctx.obj.get('gitlab', False)

def valid_release_url(release_url):
    if not GITLAB:
        return valid_github_release_url(release_url)
    else:
        return valid_gitlab_release_url(release_url)

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
    
def git_repo_file(repo, tag, filename):
    if not GITLAB:
        return github_repo_file(repo, tag, filename)
    else:
        return gitlab_repo_file(repo, tag, filename)
    
def git_release_assets(repo, tag, account_name=None, all_assets=False):
    if not GITLAB:
        return github_release_assets(account_name,repo, tag,  all_assets)
    else:
        return gitlab_release_assets(repo, tag, all_assets)
