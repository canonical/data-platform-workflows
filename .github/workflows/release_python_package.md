Workflow files: [release_python_package_part1.yaml](release_python_package_part1.yaml), [release_python_package_part2.yaml](release_python_package_part2.yaml)

## Usage
### Step 1: Use [poetry-dynamic-versioning](https://github.com/mtkennerly/poetry-dynamic-versioning)
In the Python package's `pyproject.toml`:
- a. Set version
  ```toml
  [tool.poetry]
  version = "0.0.0"  # Overriden by poetry-dynamic-versioning
  ```
- b. Configure these settings
  ```toml
  [tool.poetry-dynamic-versioning]
  enable = true
  vcs = "git"
  dirty = true
  strict = true
  ```
- c. Under `build-system`, add `"poetry-dynamic-versioning>=1.0.0,<2.0.0"` to `requires` and set `build-backend`. For example:
  ```toml
  [build-system]
  requires = ["poetry-core>=1.0.0,<2.0.0", "poetry-dynamic-versioning>=1.0.0,<2.0.0"]
  build-backend = "poetry_dynamic_versioning.backend"
  ```

### Step 2: Add `release.yaml` to `.github/workflows`
```yaml
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.
name: Release to PyPI

on:
  push:
    branches:
      - main

concurrency:
  # Prevent race conditions (if multiple commits have been pushed since the last release)
  group: dpw-release-python-package-${{ github.ref }}
  cancel-in-progress: true

jobs:
  release-part1:
    name: Release to PyPI (part 1)
    uses: canonical/data-platform-workflows/.github/workflows/release_python_package_part1.yaml@v0.0.0
    permissions:
      contents: write  # Needed to create git tag

  # Separate job needed to workaround https://github.com/pypi/warehouse/issues/11096
  release-trusted-publishing:
    name: Release to PyPI (trusted publishing)
    needs:
      - release-part1
    runs-on: ubuntu-latest
    timeout-minutes: 5
    environment: production
    steps:
      - name: Download all the dists
        uses: actions/download-artifact@v4
        with:
          name: ${{ needs.release-part1.outputs.artifact-name }}
          path: dist/
      - name: Publish to PyPI
        uses: pypa/gh-action-pypi-publish@release/v1
    permissions:
      id-token: write  # Needed for PyPI trusted publishing

  release-part2:
    name: Release to PyPI (part 2)
    needs:
      - release-part1
      - release-trusted-publishing
    uses: canonical/data-platform-workflows/.github/workflows/release_python_package_part2.yaml@v0.0.0
    with:
      git-tag: ${{ needs.release-part1.outputs.git-tag }}
    permissions:
      contents: write  # Needed to create GitHub release
```

### Step 3: Add `check_pr.yaml` file to `.github/workflows/`
```yaml
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.
name: Check pull request

on:
  pull_request:
    types:
      - opened
      - edited
    branches:
      - main

jobs:
  check-pr:
    name: Check pull request
    uses: canonical/data-platform-workflows/.github/workflows/check_python_package_pr.yaml@v0.0.0
```

### Step 4: Configure GitHub repository settings
- a. Only allow squash merging: https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/configuring-pull-request-merges/configuring-commit-squashing-for-pull-requests
- b. In the squash merge setting, change the "Default commit message" to include the pull request title (i.e. pick one of `Pull request title`, `Pull request title and commit details`, or `Pull request title and description`)

### Step 5: Configure PyPI trusted publishing
- a. Go to https://pypi.org/manage/account/publishing/
- b. Go to the "Add a new pending publisher" section
- c. Use the value of `project.name` in the Python package's `pyproject.toml` for "PyPI Project Name"
- d. Use `release.yaml` for "Workflow name"
- e. Use `production` for "Environment name"
- f. Fill out "Owner" and "Repository name"

### Step 6: Create initial git tag
Immediately before the changes required by the previous steps are merged/pushed to the `main` branch, run
```
git fetch origin
git tag v0.1.0 origin/main --annotate
git push origin v0.1.0
```
To start at a different initial version, replace `v0.1.0` with a different semantic version

### Step 7: Merge or push
Merge/push the changes required by the previous steps. Prefix the PR title or commit message with `patch:`—if this is the first version of the package (otherwise, another prefix may appropriate)
