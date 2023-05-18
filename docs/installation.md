# Installation

IGA can be installed as either (or both) a command-line program on your computer or a [GitHub Action](https://docs.github.com/en/actions) in a GitHub repository.

## IGA as a normal program

Please choose an approach that suits your situation and preferences.

### Alternative 1: installing IGA using `pipx`

[Pipx](https://pypa.github.io/pipx/) lets you install Python programs in a way that isolates Python dependencies, and yet the resulting `iga` command can be run from any shell and directory &ndash; like any normal program on your computer. If you use `pipx` on your system, you can install IGA with the following command:
```sh
pipx install iga
```

Pipx can also let you run IGA directly using `pipx run iga`, although in that case, you must always prefix every IGA command with `pipx run`.  Consult the [documentation for `pipx run`](https://github.com/pypa/pipx#walkthrough-running-an-application-in-a-temporary-virtual-environment) for more information.


### Alternative 2: installing IGA using `pip`

IGA is available from the [Python package repository PyPI](https://pypi.org) and can be installed using [`pip`](https://pip.pypa.io/en/stable/installing/):
```sh
python3 -m pip install iga
```

As an alternative to getting it from [PyPI](https://pypi.org), you can install `iga` directly from GitHub:
```sh
python3 -m pip install git+https://github.com/caltechlibrary/iga.git
```

_If you already installed IGA once before_, and want to update to the latest version, add `--upgrade` to the end of either command line above.


### Alternative 3: installing IGA from sources

If  you prefer to install IGA directly from the source code, first obtain a copy by either downloading the source archive from the [IGA releases page on GitHub](https://github.com/caltechlibrary/iga/releases), or by using `git` to clone the repository to a location on your computer. For example,
```sh
git clone https://github.com/caltechlibrary/iga
```

Next, after getting a copy of the files,  run `setup.py` inside the code directory:
```sh
cd iga
python3 setup.py install
```


## IGA as a GitHub Action

A [GitHub Action](https://docs.github.com/en/actions) is a workflow that runs on GitHub's servers under control of a file in your repository. Follow these steps to create the IGA workflow file:

1. In the main branch of your GitHub repository, create a `.github/workflows` directory
2. In the `.github/workflows` directory, create a file named (e.g.) `iga.yml` and copy the [following contents](https://raw.githubusercontent.com/caltechlibrary/iga/develop/sample-workflow.yml):
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
4. Optionally, change the [values of other options (`all_assets`, `community`, etc.)](https://caltechlibrary.github.io/iga/gha-usage.html#input-parameters)
5. Save the file, commit the changes to git, and push your changes to GitHub

The sample `.yml` workflow file above is also available from the GitHub repository for IGA as file [`sample-workflow.yml`](https://github.com/caltechlibrary/iga/blob/main/sample-workflow.yml).
