# Quick-start configuration

After a successful [installation](installation.md), At mininum, IGA needs the following information to do its work:
1. (Required) The identity of the GitHub release to be sent to InvenioRDM
    * The URL of the web page on GitHub of a tagged release, _or_
    * The arguments `--account` and `--repo` together with a release tag
2. (Required) The address of the InvenioRDM server
    * The value of the environment variable `INVENIO_SERVER`, _or_
    * The value of the option `--invenio-server`
3. (Required) A Personal Access Token (PAT) for the InvenioRDM server's API
    * The value of the environment variable `INVENIO_TOKEN`, _or_
    * The value of the option `--invenio-token`
4. (Optional) A Personal Access Token for GitHub
    * The value of the environment variable `GITHUB_TOKEN`, _or_
    * The value of the option `--invenio-token`

Here's an example of using IGA with environment variables `INVENIO_SERVER`, `INVENIO_TOKEN`, and `GITHUB_TOKEN` all set, and providing the URL of a release in GitHub:
```shell
iga https://github.com/mhucka/taupe/releases/tag/v1.2.0
```

More information about other IGA options, such as how to create a new version of an existing InvenioRDM record, is provided in the [section on detailed usage information](cli-usage.md).
