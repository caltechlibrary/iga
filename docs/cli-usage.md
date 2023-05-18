# Usage (command-line)

If the [installation process](installation.md) is successful, you should end up with a program named `iga` in a location where software is normally installed on your computer.  Running `iga` should be as simple as running any other command-line program. For example, the following command should print a helpful message to your terminal:
```shell
iga --help
```

## InvenioRDM server

The server address must be provided either as the value of the option `--invenio-server` or in an environment variable named `INVENIO_SERVER`.  If the server address does not begin with `https://`, IGA will prepend it automatically.

## InvenioRDM access token

A personal access token (PAT) for making API calls to the InvenioRDM server must be also supplied when invoking IGA. The preferred method is to set the value of the environment variable `INVENIO_TOKEN`. Alternatively, you can use the option `--invenio-token` to pass the token on the command line, but **you are strongly advised to avoid this practice because it is insecure**.

To obtain a PAT from an InvenioRDM server, first log in to the server, then visit the page at `/account/settings/applications` and use the interface there to create a token. The token will be a long string of alphanumeric characters such as `OH0KYf4PGYQGnCM4b53ejSGicOC4s4YnonRVzGJbWxY`; set the value of the variable `INVENIO_TOKEN` to this string.

## GitHub access token

It _may_ be possible to run IGA without providing a GitHub access token. GitHub allows up to 60 API calls per minute when running without credentials, and though IGA makes several API calls to GitHub each time it runs, for some repositories IGA will not hit the limit. However, if you run IGA multiple times in a row or your repository has many contributors, then you may need to supply a GitHub access token. The preferred way of doing that is to set the value of the environment variable `GITHUB_TOKEN`. Alternatively, you can use the option `--github-token` to pass the token on the command line, but **you are strongly advised to avoid this practice because it is insecure**.  To obtain a PAT from GitHub, visit https://docs.github.com/en/authentication and follow the instructions for creating a "classic" personal access token.

Note that when you run IGA as a GitHub Action, you do not need to create or set a GitHub token because it is obtained automatically by the GitHub Action workflow.

## GitHub releases

A GitHub release can be specified to IGA in one of two mutually-exclusive ways:
 1. The full URL of the web page on GitHub of a tagged release. In this case,
    the URL must be the final argument on the command line invocation of IGA
    and the options `--account` and `--repo` must be omitted.
 2. A combination of _account name_, _repository name_, and _tag_. In this
    case, the final argument on the command line must be the _tag_, and in
    addition, values for the options `--account` and `--repo` must be provided.

Here's an example using approach #1 (assuming environment variables `INVENIO_SERVER`, `INVENIO_TOKEN`, and `GITHUB_TOKEN` have all been set):
```shell
iga https://github.com/mhucka/taupe/releases/tag/v1.2.0
```
and here's the equivalent using approach #2:
```shell
iga --github-account mhucka --github-repo taupe v1.2.0
```
Note that when using this form of the command, the release tag (`v1.2.0` above) must be the last item given on the command line.

## Metadata sources

The record created in InvenioRDM is constructed using information obtained using GitHub's API as well as several other APIs as needed. The information includes the following:
 * (if one exists) a `codemeta.json` file in the GitHub repository
 * (if one exists) a `CITATION.cff` file in the GitHub repository
 * data available from GitHub for the release
 * data available from GitHub for the repository
 * data available from GitHub for the account of the owner
 * data available from GitHub for the accounts of repository contributors
 * file assets associated with the GitHub release
 * data available from ORCID.org for ORCID identifiers
 * data available from ROR.org for Research Organization Registry identifiers
 * data available from DOI.org, NCBI, Google Books, & others for publications
 * data available from spdx.org for software licenses

IGA tries to use [`CodeMeta.json`](https://codemeta.github.io) first and [`CITATION.cff`](https://citation-file-format.github.io) second to fill out the fields of the InvenioRDM record. If neither of those files are present, IGA uses values from the GitHub repository instead. You can make it always use all sources of info with the option `--all-metadata`. Depending on how complete and up-to-date your `CodeMeta.json` and `CITATION.cff` are, this may or may not make the record more comprehensive and may or may not introduce redundancies or unwanted values.

To override the auto-created metadata, use the option `--read-metadata` followed by the path to a JSON file structured according to the InvenioRDM schema used by the destination server. When `--read-metadata` is provided, IGA does _not_ extract the data above, but still obtains the file assets from GitHub.

## File assets

By default, IGA attaches to the InvenioRDM record _only_ the ZIP file asset created by GitHub for the release. To make IGA attach all assets associated with the GitHub release, use the option `--all-assets`.

To upload specific file assets and override the default selections made by IGA, you can use the option `--file` followed by a path to a file to be uploaded.  You can repeat the option `--file` to upload multiple file assets. Note that if `--file` is provided, then IGA _does not use any file assets from GitHub_; it is the user's responsibility to supply all the files that should be uploaded.

If both `--read-metadata` and `--file` are used, then IGA does not actually contact GitHub for any information.

## InvenioRDM communities

To submit your record to a community, use the `--community` option together with a community name. The option `--list-communities` can be used to get a list of communities supported by the InvenioRDM server. Note that submitting a record to a community means that the record will not be finalized and will not be publicly visible when IGA finishes; instead, the record URL that you receive will be for a draft version, pending review by the community moderators.

## Draft vs. published records

If the `--community` option is not used, then by default, IGA will finalize and publish the record. To make it stop short and leave the record as a draft instead, use the option `--draft`. The draft option also takes precedence over the community option: if you use both `--draft` and `--community`, IGA will stop after creating the draft record and will _not_ submit it to the community.  (You can nevertheless submit the record to a community manually once the draft is created, by visiting the record's web page and using the InvenioRDM interface there.)

## Record versions

The option `--parent-record` can be used to indicate that the record being constructed is a new version of an existing record. This will make IGA use the InvenioRDM API for [record versioning](https://inveniordm.docs.cern.ch/releases/versions/version-v2.0.0/#versioning-support). The newly-created record will be linked to a parent record identified by the value passed to `--parent-record`. The value must be either an InvenioRDM record identifier (which is a sequence of alphanumeric characters of the form _XXXXX-XXXXX_, such as `bknz4-bch35`, generated by the InvenioRDM server), or a URL to the landing page of the record in the InvenioRDM server. (Note that such URLs end in the record identifier.) Here is an example of using this option:
```
iga --parent-record xbcd4-efgh5 https://github.com/mhucka/taupe/releases/tag/v1.2.0
```

## Other options

Running IGA with the option `--save-metadata` will make it create a metadata record, but instead of uploading the record (and any assets) to the InvenioRDM server, IGA will write the result to the given destination. This can be useful not only for debugging but also for creating a starting point for a custom metadata record: first run IGA with `--save-metadata` to save a record to a file, edit the result, then finally run IGA with the `--read-metadata` option to use the modified record to create a release in the InvenioRDM server.

The `--mode` option can be used to change the run mode. Four run modes are available: `quiet`, `normal`, `verbose`, and `debug`. The default mode is `normal`, in which IGA prints a few messages while it's working. The mode `quiet` will make it avoid printing anything unless an error occurs, the mode `verbose` will make it print a detailed trace of what it is doing, and the mode `debug` will make IGA even more verbose. In addition, in `debug` mode, IGA will drop into the `pdb` debugger if it encounters an exception during execution. On Linux and macOS, debug mode also installs a signal handler on signal USR1 that causes IGA to drop into the `pdb` debugger if the signal USR1 is received. (Use `kill -USR1 NNN`, where NNN is the IGA process id.)

By default, informational output is sent to the standard output (normally the terminal console). The option `--log-dest` can be used to send the output to the given destination instead. The value can be `-` (i.e., a dash) to indicate console output, or it can be a file path to send the output to the file. A special exception is that even if a log destination is given, IGA will still print the final record URL to stdout.  This makes it possible to invoke IGA from scripts that capture the record URL while still saving diagnostic output in case debugging is needed.

Reading and writing large files may take a long time; on the other hand, IGA should not wait forever on network operations before reporting an error if a server or network becomes unresponsive. To balance these conflicting needs, IGA automatically scales its network timeout based on file sizes. To override its adaptive algorithm and set an explicit timeout value, use the option `--timeout` with a value in seconds.

If given the `--version` option, this program will print its version and other information, and exit without doing anything else.

Running IGA with the option `--help` will make it print help text and exit without doing anything else.

## Command-line summary

As explain above, IGA takes one required argument on the command line: either (1) the full URL of a web page on GitHub of a tagged release, or (2) a release tag name which is to be used in combination with options `--github-account` and `--github-repo`. The following table summarizes all the command line options available.

| Long&nbsp;form&nbsp;option&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp;&nbsp; | Short&nbsp;&nbsp; | Meaning | Default |  |
|------------------------|----------|--------------------------------------|---------|---|
| `--all-assets`         | `-A`     | Attach all GitHub assets | Attach only the release source ZIP| |
| `--all-metadata`       | `-M`     | Include additional metadata from GitHub | Favor CodeMeta & CFF | |
| `--community` _C_      | `-c` _C_ | Submit record to RDM community _C_ | Don't submit record to any community | | 
| `--draft`              | `-d`     | Mark the RDM record as a draft | Publish record when done | |
| `--file` _F_           | `-f` _F_ | Upload local file _F_ instead of GitHub assets | Upload only GitHub assets | ⚑ |
| `--github-account` _A_ | `-a` _A_ | Look in GitHub account _A_ | Get account name from release URL | ✯ | 
| `--github-repo` _R_    | `-r` _R_ | Look in GitHub repository _R_ of account _A_ | Get repo name from release URL | ✯ |
| `--github-token` _T_   | `-t` _T_ | Use GitHub access token _T_| Use value in env. var. `GITHUB_TOKEN` | |
| `--help`               | `-h`     | Print help info and exit | | |
| `--invenio-server` _S_ | `-s` _S_ | Send record to InvenioRDM server at address _S_ | Use value in env. var. `INVENIO_SERVER` | | 
| `--invenio-token` _K_  | `-k` _K_ | Use InvenioRDM access token _K_ | Use value in env. var. `INVENIO_TOKEN` | | 
| `--list-communities`   | `-L`     | List communities available for use with `--community` | | |
| `--log-dest` _L_       | `-l` _L_ | Write log output to destination _L_ | Write to terminal | ⚐ |
| `--mode` _M_           | `-m` _M_ | Run in mode `quiet`, `normal`, `verbose`, or `debug` | `normal` | |
| `--open`               | `-o`     | Open record's web page in a browser when done | Do nothing when done | |
| `--parent-record` _N_  | `-p` _N_ | Make this a new version of existing record _N_ | New record is unrelated to other records | ❖ |
| `--read-metadata` _R_  | `-R` _R_ | Read metadata record from file _R_; don\'t build one | Build metadata record | |
| `--save-metadata` _D_  | `-S` _D_ | Save metadata record to file _D_; don\'t upload it | Upload to InvenioRDM server | |
| `--timeout` _X_        | `-T` _X_ | Wait on network operations a max of _X_ seconds | Auto-adjusted based on file size | |
| `--version`            | `-V`     | Print program version info and exit | | |

⚑ &nbsp; Can repeat the option to specify multiple files.<br>
⚐ &nbsp; To write to the console, use the character `-` as the value of _OUT_; otherwise, _OUT_ must be the name of a file where the output should be written.<br>
✯ &nbsp; When using `--github-account` and `--github-repo`, the last argument on the command line must be a release tag name.<br>
❖ &nbsp; The record identifier must be given either as a sequence of alphanumeric characters of the form _XXXXX-XXXXX_ (e.g., `bknz4-bch35`), or as a URL to the landing page of an existing record in the InvenioRDM server.

## Return values

This program exits with a return status code of 0 if no problem is encountered.  Otherwise, it returns a nonzero status code. The following table lists the possible values:

| Code | Meaning                                                  |
|:----:|----------------------------------------------------------|
| 0    | success &ndash; program completed normally               |
| 1    | interrupted                                              |
| 2    | encountered a bad or missing value for an option         |
| 3    | encountered a problem with a file or directory           |
| 4    | encountered a problem interacting with GitHub            |
| 5    | encountered a problem interacting with InvenioRDM        |
| 6    | the personal access token was rejected                   |
| 7    | an exception or fatal error occurred                     |
