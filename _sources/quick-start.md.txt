# Quick start

After a successful [installation](installation.md) of IGA, here is how you can get started quickly.


## Essential configuration

IGA needs only a few pieces of information to do its work, and the information can be provided in more than one way:
1. (Required) The identity of the GitHub release. Methods available:
    * The URL of the web page of a tagged release in GitHub, _or_
    * Values for the options `--account`, `--repo`, and a release tag.
2. (Required) The address of the InvenioRDM server. Methods available:
    * The value of the environment variable `INVENIO_SERVER`, _or_
    * The value of the option `--invenio-server`
3. (Required) A Personal Access Token (PAT) for the InvenioRDM server. Methods available:
    * The value of the environment variable `INVENIO_TOKEN`, _or_
    * The value of the option `--invenio-token`
4. (Optional) A Personal Access Token for GitHub. Methods available:
    * The value of the environment variable `GITHUB_TOKEN`, _or_
    * The value of the option `--github-token`

More information about other IGA options, such as how to create a new version of an existing InvenioRDM record, is provided in the section on [detailed usage information](cli-usage.md).


## Examples of use

A common way of configuring IGA is to set environment variables in your shell script or your interactive shell. Here is an example using Bash shell syntax, with realistic-looking but fake
 token values:
```shell
export INVENIO_SERVER=https://data.caltech.edu
export INVENIO_TOKEN=qKLoOH0KYf4D98PGYQGnC09hiuqw3Y1SZllYnonRVzGJbWz2
export GITHUB_TOKEN=ghp_wQXp6sy3AsKyyEo4l9esHNxOdo6T34Zsthz
```

Once these environment variables set in your shell, you can more easily invoke IGA. Usage can be as simple as providing a URL for a release in GitHub. For example:
```shell
iga https://github.com/mhucka/taupe/releases/tag/v1.2.0
```

If you give the option `--open` (or `-o` for short) to IGA, it will open the newly-created InvenioRDM entry in your default web browser when it's done:
```shell
iga -o https://github.com/mhucka/taupe/releases/tag/v1.2.0
```

If you want the record to be only a draft and not a final version (perhaps so that you can inspect the result and edit it before finalizing it), use the option `--draft` (or `-d` for short):
```shell
iga -d -o https://github.com/mhucka/taupe/releases/tag/v1.2.0
```

More options and examples can be found in the section on [detailed usage information](cli-usage.md).
