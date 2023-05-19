# IGA<img width="12%" align="right" src="https://github.com/caltechlibrary/iga/raw/main/docs/_static/media/cloud-upload.png">

IGA is the _InvenioRDM GitHub Archiver_, a standalone program as well as a [GitHub Action](https://github.com/marketplace/actions/iga) that lets you automatically archive GitHub software releases in an [InvenioRDM](https://inveniosoftware.org/products/rdm/) repository.

[![Latest release](https://img.shields.io/github/v/release/caltechlibrary/iga.svg?style=flat-square&color=b44e88&label=Latest%20release)](https://github.com/caltechlibrary/iga/releases)
[![License](https://img.shields.io/badge/License-BSD--like-lightgrey.svg?style=flat-square)](https://github.com/caltechlibrary/iga/LICENSE)
[![Python](https://img.shields.io/badge/Python-3.9+-brightgreen.svg?style=flat-square)](https://www.python.org/downloads/release/python-390/)
[![PyPI](https://img.shields.io/pypi/v/iga.svg?style=flat-square&color=orange&label=PyPI)](https://pypi.org/project/iga/)


## Table of contents

* [Introduction](#introduction)
* [Installation](#installation)
* [Quick start](#quick-start)
* [Usage](#usage)
* [Known issues and limitations](#known-issues-and-limitations)
* [Getting help](#getting-help)
* [Contributing](#contributing)
* [License](#license)
* [Acknowledgments](#authors-and-acknowledgments)


## Introduction

[InvenioRDM](https://inveniosoftware.org/products/rdm/) is the basis for many institutional repositories such as [CaltechDATA](https://data.caltech.edu) that enable users to preserve software and data sets in long-term archive. Though such repositories are critical resources, creating detailed records and uploading assets can be a tedious and error-prone process if done manually. This is where the [_InvenioRDM GitHub Archiver_](https://github.com/caltechlibrary/iga) (IGA) comes in.

IGA creates metadata records and sends releases from GitHub to an InvenioRDM-based repository server. IGA can be invoked from the command line; it also can be set up as a [GitHub Action](https://docs.github.com/en/actions) to archive GitHub releases automatically for a repository each time they are made.

<p align=center>
<img align="middle" src="https://github.com/caltechlibrary/iga/raw/main/docs/_static/media/example-github-release.jpg" width="40%">
<span style="font-size: 150%">➜</span>
<img align="middle" src="https://github.com/caltechlibrary/iga/raw/main/docs/_static/media/example-record-landing-page.jpg" width="40%">
</p>

IGA offers many notable features:
* Automatic metadata extraction from GitHub plus [`codemeta.json`](https://codemeta.github.io) and [`CITATION.cff`](https://citation-file-format.github.io) files
* Thorough coverage of [InvenioRDM record metadata](https://inveniordm.docs.cern.ch/reference/metadata) using painstaking procedures
* Recognition of identifiers in CodeMeta & CFF files: [ORCID](https://orcid.org), [DOI](https://www.doi.org),  [PMCID](https://www.ncbi.nlm.nih.gov/pmc/about/public-access-info/), and more
* Automatic lookup of publication data in [DOI.org](https://www.doi.org), [PubMed]((https://www.ncbi.nlm.nih.gov/pmc/about/public-access-info/)), Google, and other sources
* Automatic lookup of organization names in [ROR](https://ror.org) (assuming ROR id's are provided)
* Automatic lookup of human names in [ORCID.org](https://orcid.org) (assuming ORCID id's are provided)
* Automatic splitting of human names into family & given names using [ML](https://en.wikipedia.org/wiki/Machine_learning) methods
* Support for InvenioRDM [communities](https://invenio-communities.readthedocs.io/en/latest/)
* Support for overriding the record that IGA creates, for complete control if you need it
* Support for using the GitHub API without a [GitHub access token](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token) in simple cases
* Extensive use of logging so you can see what's going on under the hood


## Installation

IGA can be installed as either (or both) a command-line program on your computer or a [GitHub Action](https://docs.github.com/en/actions) in a GitHub repository.

### IGA as a standalone program

Please choose an approach that suits your situation and preferences.

<details><summary><h4><i>Alternative 1: using <code>pipx</code></i></h4></summary>

[Pipx](https://pypa.github.io/pipx/) lets you install Python programs in a way that isolates Python dependencies, and yet the resulting `iga` command can be run from any shell and directory &ndash; like any normal program on your computer. If you use `pipx` on your system, you can install IGA with the following command:
```sh
pipx install iga
```

Pipx can also let you run IGA directly using `pipx run iga`, although in that case, you must always prefix every IGA command with `pipx run`.  Consult the [documentation for `pipx run`](https://github.com/pypa/pipx#walkthrough-running-an-application-in-a-temporary-virtual-environment) for more information.
</details>

<details><summary><h4><i>Alternative 2: using <code>pip</code></i></h4></summary>

IGA is available from the [Python package repository PyPI](https://pypi.org) and can be installed using [`pip`](https://pip.pypa.io/en/stable/installing/):
```sh
python3 -m pip install iga
```

As an alternative to getting it from [PyPI](https://pypi.org), you can install `iga` directly from GitHub:
```sh
python3 -m pip install git+https://github.com/caltechlibrary/iga.git
```

_If you already installed IGA once before_, and want to update to the latest version, add `--upgrade` to the end of either command line above.
</details>

<details><summary><h4><i>Alternative 3: from sources</i></h4></summary>

If  you prefer to install IGA directly from the source code, first obtain a copy by either downloading the source archive from the [IGA releases page on GitHub](https://github.com/caltechlibrary/iga/releases), or by using `git` to clone the repository to a location on your computer. For example,
```sh
git clone https://github.com/caltechlibrary/iga
```

Next, after getting a copy of the files,  run `setup.py` inside the code directory:
```sh
cd iga
python3 setup.py install
```
</details>

After installation, a program named `iga` should end up in a location where other command-line programs are installed on your computer.  Test it by running the following command in a shell:
```shell
iga --help
```


### IGA as a GitHub Action

A [GitHub Action](https://docs.github.com/en/actions) is a workflow that runs on GitHub's servers under control of a file in your repository. Follow these steps to create the IGA workflow file:

1. In the main branch of your GitHub repository, create a `.github/workflows` directory
2. In the `.github/workflows` directory, create a file named (e.g.) `iga.yml` and copy the [following contents](https://raw.githubusercontent.com/caltechlibrary/iga/develop/sample-workflow.yml) into it:
    ```yaml
    name: InvenioRDM GitHub Archiver

    env:
      # 👋🏻 Set the next variable to your InvenioRDM server address 👋🏻
      INVENIO_SERVER: https://your-invenio-server.org

      # Set to an InvenioRDM record ID to mark releases as new versions.
      parent_record: none

      # The remaining variables are other IGA options. Please see the docs.
      community:     none
      draft:         false
      all_assets:    false
      all_metadata:  false
      debug:         false

    # ~~~~~~~~~~~~~~~~ The rest of this file should be left as-is. ~~~~~~~~~~~~~~~~

    on:
      release:
        types: [published]
      workflow_dispatch:
        inputs:
          release_tag:
            description: "The release tag (empty = latest):"
          draft:
            default: false
            description: "Mark the InvenioRDM record as a draft:"
          parent_record:
            description: "ID of parent record (for versioning):"
          community:
            description: "Name of InvenioRDM community (if any):"
          all_assets:
            default: false
            description: "Attach all GitHub assets:"
          all_metadata:
            default: false
            description: "Include additional GitHub metadata:"
          debug:
            default: false
            description: "Print debug info in the GitHub log:"
    jobs:
      Send_to_InvenioRDM:
        runs-on: ubuntu-latest
        steps:
          - uses: caltechlibrary/iga@main
            with:
              INVENIO_SERVER: ${{env.INVENIO_SERVER}}
              INVENIO_TOKEN:  ${{secrets.INVENIO_TOKEN}}
              all_assets:     ${{github.event.inputs.all_assets || env.all_assets}}
              all_metadata:   ${{github.event.inputs.all_metadata || env.all_metadata}}
              debug:          ${{github.event.inputs.debug || env.debug}}
              draft:          ${{github.event.inputs.draft || env.draft}}
              community:      ${{github.event.inputs.community || env.community}}
              parent_record:  ${{github.event.inputs.parent_record || env.parent_record}}
              release_tag:    ${{github.event.inputs.release_tag || 'latest'}}
    ```
3. **Edit the value of the `INVENIO_SERVER` variable (line 5 above)** ↑
4. Optionally, change the values of other options (`parent_record`, `community`, etc.)
5. Save the file, commit the changes to git, and push your changes to GitHub


## Quick start

No matter whether IGA is run locally on your computer or as a GitHub Action, in both cases it must be provided with a personal access token (PAT) for your InvenioRDM server. Getting one 
is the first step.

### Getting an InvenioRDM token

<img src="https://github.com/caltechlibrary/iga/raw/main/docs/_static/media/get-invenio-pat.png" width="60%" align="right">

1. Log in to your InvenioRDM account
2. Go to the _Applications_ page in your account profile
3. Click the <kbd>New token</kbd> button next to "Personal access tokens"
4. On the page that is shown after you click that button, name your token (the name does not matter) and click the <kbd>Create</kbd> button
5. After InvenioRDM creates and shows you the token, **copy it to a safe location** because InvenioRDM will not show it again

### Configuring and running IGA locally

To send a GitHub release to your InvenioRDM server, IGA needs this information:
1. (Required) The identity of the GitHub release to be archived
2. (Required) The address of the destination InvenioRDM server
3. (Required) A personal access token for InvenioRDM (from [above](#getting-an-inveniordm-token))
4. (Optional) A [personal access token for GitHub](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/creating-a-personal-access-token)

The identity of the GitHub release is always given as an argument to IGA on the command line; the remaining values can be provided either via command-line options or environment variables. One approach is to set environment variables in shell scripts or your interactive shell. Here is an example using Bash shell syntax, with fake token values:
```shell
export INVENIO_SERVER=https://data.caltech.edu
export INVENIO_TOKEN=qKLoOH0KYf4D98PGYQGnC09hiuqw3Y1SZllYnonRVzGJbWz2
export GITHUB_TOKEN=ghp_wQXp6sy3AsKyyEo4l9esHNxOdo6T34Zsthz
```

Once these are set, use of IGA can be as simple as providing a URL for a release in GitHub. For example, the following command creates a draft record (the `-d` option is short for `--draft`) for another project in GitHub and tells IGA to open (the `-o` option is short for `--open`) the newly-created InvenioRDM entry in a web browser:
```shell
iga -d -o https://github.com/mhucka/taupe/releases/tag/v1.2.0
```

More options are described in the section on [detailed usage information](#usage) below.


### Configuring and running IGA as a GitHub Action

After doing the [GitHub Action installation](#as-a-github-action) steps and [obtaining an InvenioRDM token](#getting-an-inveniordm-token), one more step is needed: the token must be stored as a "secret" in your GitHub repository.

1. Go to the _Settings_ page of your GitHub repository<p align="center"><img src="https://github.com/caltechlibrary/iga/raw/main/docs/_static/media/github-tabs.png" width="85%"></p>
2. In the left-hand sidebar, find _Secrets and variables_ in the Security section, click on it to reveal _Actions_ underneath, then click on _Actions_<p align="center"><img src="https://github.com/caltechlibrary/iga/raw/main/docs/_static/media/github-sidebar-secrets.png" width="40%"></p>
3. In the next page, click the green <kbd>New repository secret</kbd> button<p align="center"><img src="https://github.com/caltechlibrary/iga/raw/main/docs/_static/media/github-secrets.png" width="60%"></p>
4. Name the variable `INVENIO_TOKEN` and paste in your InvenioRDM token
5. Finish by clicking the green <kbd>Add secret</kbd> button

#### Testing the workflow

After setting up the workflow and storing the InvenioRDM token in your repository on GitHub, it's a good idea to run the workflow manually to test that it works as expected.

1. Go to the _Actions_ tab in your repository and click on the name of the workflow in the sidebar on the left<p align="center"><img src="https://github.com/caltechlibrary/iga/raw/main/docs/_static/media/github-run-workflow.png" width="90%"></p>
2. Click the <kbd>Run workflow</kbd> button in the right-hand side of the blue strip
3. In the pull-down, change the value of "Mark the record as a draft" to `true`<p align="center"><img src="https://github.com/caltechlibrary/iga/raw/main/docs/_static/media/github-workflow-options-circled.png" width="40%"></p>
4. Click the green <kbd>Run workflow</kbd> button near the bottom
5. Refresh the web page and a new line will be shown named after your workflow file<p align="center"><img src="https://github.com/caltechlibrary/iga/raw/main/docs/_static/media/github-running-workflow.png" width="90%"></p>
6. Click the title of the workflow to see the IGA workflow progress and results


#### Running the workflow when releasing software

Once the personal access token from InvenioRDM is stored as a GitHub secret, the workflow should run automatically every time a new release is made on GitHub &ndash; no further action should be needed. You can check the results (and look for errors if something went wrong) by going to the _Actions_ tab in your GitHub repository.


## Usage

This section provides detailed information about IGA's operation and options to control it.

### Identifying the InvenioRDM server

The server address must be provided either as the value of the option `--invenio-server` or in an environment variable named `INVENIO_SERVER`.  If the server address does not begin with `https://`, IGA will prepend it automatically.

### Providing an InvenioRDM access token

A personal access token (PAT) for making API calls to the InvenioRDM server must be also supplied when invoking IGA. The preferred method is to set the value of the environment variable `INVENIO_TOKEN`. Alternatively, you can use the option `--invenio-token` to pass the token on the command line, but **you are strongly advised to avoid this practice because it is insecure**.

To obtain a PAT from an InvenioRDM server, first log in to the server, then visit the page at `/account/settings/applications` and use the interface there to create a token. The token will be a long string of alphanumeric characters such as `OH0KYf4PGYQGnCM4b53ejSGicOC4s4YnonRVzGJbWxY`; set the value of the variable `INVENIO_TOKEN` to this string.

### Providing a GitHub access token

It _may_ be possible to run IGA without providing a GitHub access token. GitHub allows up to 60 API calls per minute when running without credentials, and though IGA makes several API calls to GitHub each time it runs, for some repositories IGA will not hit the limit. However, if you run IGA multiple times in a row or your repository has many contributors, then you may need to supply a GitHub access token. The preferred way of doing that is to set the value of the environment variable `GITHUB_TOKEN`. Alternatively, you can use the option `--github-token` to pass the token on the command line, but **you are strongly advised to avoid this practice because it is insecure**.  To obtain a PAT from GitHub, visit https://docs.github.com/en/authentication and follow the instructions for creating a "classic" personal access token.

Note that when you run IGA as a GitHub Action, you do not need to create or set a GitHub token because it is obtained automatically by the GitHub Action workflow.

### Specifying a GitHub release

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

### Gathering metadata for an InvenioRDM record

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

### Specifying GitHub file assets

By default, IGA attaches to the InvenioRDM record _only_ the ZIP file asset created by GitHub for the release. To make IGA attach all assets associated with the GitHub release, use the option `--all-assets`.

To upload specific file assets and override the default selections made by IGA, you can use the option `--file` followed by a path to a file to be uploaded.  You can repeat the option `--file` to upload multiple file assets. Note that if `--file` is provided, then IGA _does not use any file assets from GitHub_; it is the user's responsibility to supply all the files that should be uploaded.

If both `--read-metadata` and `--file` are used, then IGA does not actually contact GitHub for any information.

### Handling communities

To submit your record to a community, use the `--community` option together with a community name. The option `--list-communities` can be used to get a list of communities supported by the InvenioRDM server. Note that submitting a record to a community means that the record will not be finalized and will not be publicly visible when IGA finishes; instead, the record URL that you receive will be for a draft version, pending review by the community moderators.

### Indicating draft versus published records

If the `--community` option is not used, then by default, IGA will finalize and publish the record. To make it stop short and leave the record as a draft instead, use the option `--draft`. The draft option also takes precedence over the community option: if you use both `--draft` and `--community`, IGA will stop after creating the draft record and will _not_ submit it to the community.  (You can nevertheless submit the record to a community manually once the draft is created, by visiting the record's web page and using the InvenioRDM interface there.)

### Versioning records

The option `--parent-record` can be used to indicate that the record being constructed is a new version of an existing record. This will make IGA use the InvenioRDM API for [record versioning](https://inveniordm.docs.cern.ch/releases/versions/version-v2.0.0/#versioning-support). The newly-created record will be linked to a parent record identified by the value passed to `--parent-record`. The value must be either an InvenioRDM record identifier (which is a sequence of alphanumeric characters of the form _XXXXX-XXXXX_, such as `bknz4-bch35`, generated by the InvenioRDM server), or a URL to the landing page of the record in the InvenioRDM server. (Note that such URLs end in the record identifier.) Here is an example of using this option:
```
iga --parent-record xbcd4-efgh5 https://github.com/mhucka/taupe/releases/tag/v1.2.0
```

### Other options recognized by IGA

Running IGA with the option `--save-metadata` will make it create a metadata record, but instead of uploading the record (and any assets) to the InvenioRDM server, IGA will write the result to the given destination. This can be useful not only for debugging but also for creating a starting point for a custom metadata record: first run IGA with `--save-metadata` to save a record to a file, edit the result, then finally run IGA with the `--read-metadata` option to use the modified record to create a release in the InvenioRDM server.

The `--mode` option can be used to change the run mode. Four run modes are available: `quiet`, `normal`, `verbose`, and `debug`. The default mode is `normal`, in which IGA prints a few messages while it's working. The mode `quiet` will make it avoid printing anything unless an error occurs, the mode `verbose` will make it print a detailed trace of what it is doing, and the mode `debug` will make IGA even more verbose. In addition, in `debug` mode, IGA will drop into the `pdb` debugger if it encounters an exception during execution. On Linux and macOS, debug mode also installs a signal handler on signal USR1 that causes IGA to drop into the `pdb` debugger if the signal USR1 is received. (Use `kill -USR1 NNN`, where NNN is the IGA process id.)

By default, informational output is sent to the standard output (normally the terminal console). The option `--log-dest` can be used to send the output to the given destination instead. The value can be `-` (i.e., a dash) to indicate console output, or it can be a file path to send the output to the file. A special exception is that even if a log destination is given, IGA will still print the final record URL to stdout.  This makes it possible to invoke IGA from scripts that capture the record URL while still saving diagnostic output in case debugging is needed.

Reading and writing large files may take a long time; on the other hand, IGA should not wait forever on network operations before reporting an error if a server or network becomes unresponsive. To balance these conflicting needs, IGA automatically scales its network timeout based on file sizes. To override its adaptive algorithm and set an explicit timeout value, use the option `--timeout` with a value in seconds.

If given the `--version` option, this program will print its version and other information, and exit without doing anything else.

Running IGA with the option `--help` will make it print help text and exit without doing anything else.

### Summary of command-line options

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

### Return values

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


## Known issues and limitations

The following are known issues and limitations.
* As of mid-2023, InvenioRDM requires names of record creators and other contributors to be split into given (first) and family (surname). This is problematic for multiple reasons. The first is that mononyms are common in many countries: a person's name may legitimately be only a single word which is not conceptually a "given" or "family" name.  To compound the difficulty for IGA, names are stored as single fields in GitHub account metadata, so unless a repository has a `codemeta.json` or `CITATION.cff` file (which allow authors more control over how they want their names represented), IGA is forced to try to split the single GitHub name string into two parts. _A foolproof algorithm for doing this does not exist_, so IGA will sometimes get it wrong. (That said, IGA goes to extraordinary lengths to try to do a good job.)
* Some accounts on GitHub are software automation or "bot" accounts but are not labeled as such. These accounts are generally indistinguishable from human accounts on GitHub. If such an account is the creator of a release in GitHub, and IGA has to use its name-splitting algorithm on the name of the account, it may produce a nonsensical result. For example, it might turn "Travis CI" into an entry with a first name of "Travis" and last name of "CI". 


## Getting help

If you find an issue, please submit it in [the GitHub issue tracker](https://github.com/caltechlibrary/iga/issues) for this repository.


## Contributing

Your help and participation in enhancing IGA is welcome!  Please visit the [guidelines for contributing](CONTRIBUTING.md) for some tips on getting started.


## License

Software produced by the Caltech Library is Copyright © 2023 California Institute of Technology.  This software is freely distributed under a BSD-style license.  Please see the [LICENSE](LICENSE) file for more information.

## Acknowledgments

This work was funded by the California Institute of Technology Library.

IGA uses multiple other open-source packages, without which it would have taken much longer to write the software. I want to acknowledge this debt. In alphabetical order, the packages are:
* [Aenum](https://github.com/ethanfurman/aenum) &ndash; package for advanced enumerations
* [Arrow](https://pypi.org/project/arrow/) &ndash; a library for creating & manipulating dates
* [Boltons](https://github.com/mahmoud/boltons/) &ndash; package of miscellaneous Python utilities
* [caltechdata_api](https://github.com/caltechlibrary/caltechdata_api) &ndash; package for using the CaltechDATA API
* [CommonPy](https://github.com/caltechlibrary/commonpy) &ndash; a collection of commonly-useful Python functions
* [demoji](https://github.com/bsolomon1124/demoji) &ndash; find or remove emojis from text
* [dirtyjson](https://github.com/codecobblers/dirtyjson) &ndash; JSON decoder that copes with problematic JSON files and reports useful error messages
* [flake8](https://github.com/pycqa/flake8) &ndash; Python code linter and style analyzer
* [httpx](https://www.python-httpx.org) &ndash; HTTP client library that supports HTTP/2
* [humanize](https://github.com/jmoiron/humanize) &ndash; make numbers more easily readable by humans
* [idutils](https://github.com/inveniosoftware/idutils) &ndash; package for validating and normalizing various kinds of persistent identifiers
* [ipdb](https://github.com/gotcha/ipdb) &ndash; the IPython debugger
* [iptools](https://github.com/bd808/python-iptools) &ndash; utilities for dealing with IP addresses
* [isbnlib](https://github.com/xlcnd/isbnlib) &ndash; utilities for dealing with ISBNs
* [json5](https://github.com/dpranke/pyjson5) &ndash; extended JSON format parser
* [latexcodec](https://github.com/mcmtroffaes/latexcodec) &ndash; lexer and codec to work with LaTeX code in Python
* [linkify-it-py](https://github.com/tsutsu3/linkify-it-py) &ndash; a link recognition library with full unicode support
* [lxml](https://lxml.de) &ndash; an XML parsing library
* [Markdown](https://python-markdown.github.io) &ndash; Python package for working with Markdown
* [markdown-checklist](https://github.com/FND/markdown-checklist) &ndash; GitHub-style checklist extension for Python Markdown package
* [mdx-breakless-lists](https://github.com/adamb70/mdx-breakless-lists) &ndash; GitHub-style Markdown lists that don't require a line break above them
* [mdx_linkify](https://github.com/daGrevis/mdx_linkify) &ndash; extension for Python Markdown will convert text that look like links to HTML anchors
* [MyST-parser](https://github.com/executablebooks/MyST-Parser) &ndash; A Sphinx and Docutils extension to parse an extended version of Markdown
* [nameparser](https://github.com/derek73/python-nameparser) &ndash; package for parsing human names into their individual components
* [probablepeople](https://github.com/datamade/probablepeople) &ndash; package for parsing names into components using ML-based techniques
* [pybtex](https://pybtex.org) &ndash; BibTeX parser and formatter
* [pybtex-apa7-style]() &ndash; plugin for [pybtex](https://pybtex.org) that provides APA7 style formatting
* [pymdown-extensions](https://github.com/facelessuser/pymdown-extensions) &ndash; extensions for Python Markdown
* [pytest](https://docs.pytest.org/en/stable/) &ndash; testing framework
* [pytest-cov](https://github.com/pytest-dev/pytest-cov) &ndash; coverage reports for use with `pytest`
* [pytest-mock](https://pypi.org/project/pytest-mock/) &ndash; wrapper around the `mock` package for use with `pytest`
* [PyYAML](https://pyyaml.org) &ndash; YAML parser
* [Rich](https://github.com/Textualize/rich) &ndash; library for writing styled text to the terminal
* [rich-click](https://github.com/ewels/rich-click) &ndash; CLI interface built on top of [Rich](https://github.com/Textualize/rich)
* [setuptools](https://github.com/pypa/setuptools) &ndash; library for `setup.py`
* [Sidetrack](https://github.com/caltechlibrary/sidetrack) &ndash; simple debug logging/tracing package
* [spaCy](https://spacy.io) &ndash; Natural Language Processing package
* [spacy-alignments](https://github.com/explosion/spacy-alignments) &ndash; alternate alignments for [spaCy](https://spacy.io)
* [spacy-legacy](https://pypi.org/project/spacy-legacy/) &ndash; [spaCy](https://spacy.io) legacy functions and architectures for backwards compatibility
* [spacy-loggers](https://github.com/explosion/spacy-loggers) &ndash; loggers for [spaCy](https://spacy.io)
* [spacy-pkuseg](https://github.com/explosion/spacy-pkuseg) &ndash; Chinese word segmentation toolkit for [spaCy](https://spacy.io)
* [spacy-transformers](https://spacy.io) &ndash; pretrained Transformers for [spaCy](https://spacy.io)
* [Sphinx](https://www.sphinx-doc.org/en/master/) &ndash; documentation generator for Python
* [sphinx-autobuild](https://pypi.org/project/sphinx-autobuild/) &ndash; rebuild Sphinx docs automatically
* [sphinx-material](https://bashtage.github.io/sphinx-material/) &ndash; a responsive Material Design theme for Sphinx
* [sphinxcontrib-mermaid](https://github.com/mgaitan/sphinxcontrib-mermaid) &ndash; support Mermaid diagrams in Sphinx docs
* [StringDist](https://github.com/obulkin/string-dist) &ndash; library for calculating string distances
* [Twine](https://github.com/pypa/twine) &ndash; utilities for publishing Python packages on [PyPI](https://pypi.org)
* [url-normalize](https://github.com/niksite/url-normalize) &ndash; URI/URL normalization utilities
* [validators](https://github.com/kvesteri/validators) &ndash; data validation package for Python
* [wheel](https://pypi.org/project/wheel/) &ndash; setuptools extension for building wheels

<div align="center">
  <br>
  <a href="https://www.caltech.edu">
    <img width="100" height="100" src="https://github.com/caltechlibrary/iga/raw/main/.graphics/caltech-round.png">
  </a>
</div>
