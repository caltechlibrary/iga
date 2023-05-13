# Quick start

No matter whether IGA is run locally on your computer or as a GitHub Action, in both cases it must be provided with a personal access token (PAT) for your InvenioRDM server. Getting one is the first step.

### Getting an InvenioRDM token

<img src="https://github.com/caltechlibrary/iga/raw/main/docs/_static/media/get-invenio-pat.png" width="60%" align="right">

1. Log in to your InvenioRDM account.
2. Find the _Applications_ page for your account.
3. Click the <kbd>New token</kbd> button next to "Personal access tokens" on the _Applications_ page.
4. Name your token (the name does not matter) and click the <kbd>Create</kbd> button.
5. After InvenioRDM creates and displays the token, **copy it to a safe location** because InvenioRDM will not show it again.

### Configuring and running IGA locally

To send a GitHub release to your InvenioRDM server, IGA needs this information:
1. (Required) The identity of the GitHub release to be archived
2. (Required) The address of the destination InvenioRDM server
3. (Required) A personal access token for InvenioRDM (from [above](#getting-an-inveniordm-token))
4. (Optional) A [personal access token for GitHub](https://docs.github.com/en/enterprise-server@3.4/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

The identity of the GitHub release is always given as an argument to IGA on the command line; the remaining values can be provided either via command-line options or environment variables. One approach is to set environment variables in shell scripts or your interactive shell. Here is an example using Bash shell syntax, with fake token values:
```shell
export INVENIO_SERVER=https://data.caltech.edu
export INVENIO_TOKEN=qKLoOH0KYf4D98PGYQGnC09hiuqw3Y1SZllYnonRVzGJbWz2
export GITHUB_TOKEN=ghp_wQXp6sy3AsKyyEo4l9esHNxOdo6T34Zsthz
```

Once these are set, use of IGA can be as simple as providing a URL for a release in GitHub. For example, the following command creates a draft record (the `-d` option is short for `--draft`) for another project in GitHub and tells IGA to open (the `-o` option is short for `--open`) the newly-created InvenioRDM entry in a web browser:
```shell
iga -d https://github.com/mhucka/taupe/releases/tag/v1.2.0
```

More options are described in the section on [detailed usage information](cli-usage.md).


### Configuring and running IGA as a GitHub Action

After doing the [GitHub Action installation](installation.md) steps and [obtaining an InvenioRDM token](#getting-an-inveniordm-token), one more step is needed: the token must be stored as a "secret" in your GitHub repository.

1. Go to the _Settings_ page of your GitHub repository<p align="center"><img src="https://github.com/caltechlibrary/iga/raw/main/docs/_static/media/github-tabs.png" width="85%"></p>
2. In the left-hand sidebar, find _Secrets and variables_ in the Security section, click on it to reveal _Actions_ underneath, then click on _Actions_<p align="center"><img src="https://github.com/caltechlibrary/iga/raw/main/docs/_static/media/github-sidebar-secrets.png" width="40%"></p>
3. In the next page, click the green <kbd>New repository secret</kbd> button<p align="center"><img src="https://github.com/caltechlibrary/iga/raw/main/docs/_static/media/github-secrets.png" width="60%"></p>
4. Name the variable `INVENIO_TOKEN` and paste in your InvenioRDM token
5. Finish by clicking the green <kbd>Add secret</kbd> button

#### Testing the workflow

After setting up the workflow and storing the InvenioRDM token in your repository on GitHub, it's a good idea to run the workflow manually to test that it works as expected.

1. Go to the _Actions_ tab in your repository and click on the name of the workflow in the sidebar on the left<p align="center"><img src="https://github.com/caltechlibrary/iga/raw/main/docs/_static/media/github-run-workflow.png" width="90%"></p>
2. Click the <kbd>Run workflow</kbd> button in the right-hand side of the blue strip
3. In the pull-down, change the value of "Mark the record as a draft" to `true`<p align="center"><img src="https://github.com/caltechlibrary/iga/raw/main/docs/_static/media/github-workflow-options.png" width="40%"></p>
4. Click the green <kbd>Run workflow</kbd> button.
5. Refresh the web page and a new line will be shown named after your workflow file<p align="center"><img src="https://github.com/caltechlibrary/iga/raw/main/docs/_static/media/github-running-workflow.png" width="90%"></p>
6. Click that line to see the IGA workflow progress and results


#### Running the workflow when releasing software

Once the personal access token from InvenioRDM is stored as a GitHub secret, the workflow should run automatically every time a new release is made on GitHub &ndash; no further action should be needed. You can check the results (and look for errors if something went wrong) by going to the _Actions_ tab in your GitHub repository.
