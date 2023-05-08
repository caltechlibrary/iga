# Quick start

## Command-line use

If the [installation](installation.md) process is successful, you should end up with a program named `iga` in a location where software is normally installed on your computer.  Running `iga` should be as simple as running any other command-line program. For example, the following command should print a helpful message to your terminal:
```shell
iga --help
```

IGA's main purpose is to create a metadata record in an InvenioRDM server and attach a GitHub release archive to the record. IGA needs 4 pieces of information to do its work, though for simple repositories you can often get by with just 3:
1. (Required) The identity of the GitHub release to be archived
2. (Required) The address of the destination InvenioRDM server
3. (Required) A Personal Access Token (PAT) for the InvenioRDM server
4. (Optional) A Personal Access Token for GitHub

The first one (the identity of the GitHub release) is given as arguments to IGA on the command line; the rest can be provided either via command-line options or by setting environment variables. A common way of configuring IGA is to set environment variables in your shell script or your interactive shell. Here is an example using Bash shell syntax, with realistic-looking but fake token values:
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


## GitHub Action use
