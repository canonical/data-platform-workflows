Workflow file: [_promote_charms.yaml](_promote_charms.yaml)

> [!WARNING]
> Subject to **breaking changes on patch release**. `_promote_charms.yaml` is experimental & not part of the public interface.

## Limitations
This workflow currently only supports charms that implement in-place upgrades & rollbacks with [charm-refresh](https://github.com/canonical/charm-refresh) and, thus, use [tag_charm_edge.yaml](release_charm_edge.md).

All charms must be released to the same track. All charms must share an identical charm refresh compatibility version tag.

## Usage
### Step 1: Add `promote.yaml` file to `.github/workflows/`
```yaml
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.
name: Promote charms

on:
  workflow_dispatch:
    inputs:
      from-risk:
        description: Promote from this Charmhub risk
        required: true
        type: choice
        options:
          - edge
          - beta
          - candidate
      to-risk:
        description: Promote to this Charmhub risk
        required: true
        type: choice
        options:
          - beta
          - candidate
          - stable

jobs:
  promote:
    name: Promote charms
    uses: canonical/data-platform-workflows/.github/workflows/_promote_charms.yaml@v0.0.0
    with:
      track: 'latest'
      from-risk: ${{ inputs.from-risk }}
      to-risk: ${{ inputs.to-risk }}
    secrets:
      charmhub-token: ${{ secrets.CHARMHUB_TOKEN }}
    permissions:
      contents: write  # Needed to edit GitHub releases
```
### Step 2: Add `check_pr.yaml` file to `.github/workflows/`
```yaml
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.
name: Check pull request

on:
  pull_request:
    types:
      - opened
      - labeled
      - unlabeled
    branches:
      - main

jobs:
  check-pr:
    name: Check pull request
    uses: canonical/data-platform-workflows/.github/workflows/check_charm_pr.yaml@v0.0.0
```
Update `branches` to include all branches that [`release_charm_edge.yaml`](release_charm_edge.md) runs on

### Step 3: Add `.github/release.yaml` file
```yaml
changelog:
  categories:
    - title: Features
      labels:
        - enhancement
    - title: Bug fixes
      labels:
        - bug
```

### Step 4: Ensure metadata.yaml file is present
This workflow requires the charm directory (directory with charmcraft.yaml) to contain a metadata.yaml file with the `name` and `display-name` keys. For Kubernetes charms, all `oci-image` `resources` must be pinned to a sha256 digest. Syntax: https://juju.is/docs/sdk/metadata-yaml

"Unified charmcraft.yaml syntax" (where actions.yaml, charmcraft.yaml, config.yaml, and metadata.yaml are combined into a single charmcraft.yaml file) is not supported.

Rationale in [release_charm_edge.md](release_charm_edge.md#rationale)
