# Making a Release

These are the current steps for making a release of IGA

1. Work in the develop branch
2. Run `pytest -v --cov=iga -l tests/`
3. Add changes to CHANGES.md
4. Update the version number in setup.cfg
5. Update the version number in codemeta.json
6. Make a release on GitHub. This will trigger iga to run and do the release on pypi. Wait for all actions to finish.
7. Move all new commits to the v1 branch. When on the v1 branch type `git rebase develop` 
