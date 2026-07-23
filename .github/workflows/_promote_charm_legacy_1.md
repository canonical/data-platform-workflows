Workflow file: [_promote_charm_legacy_1.yaml](_promote_charm_legacy_1.yaml)

> [!WARNING]
> This workflow is **deprecated** and should only be used for existing legacy tracks that do not have charm refresh compatibility version tags. For new tracks, [_promote_charms.yaml](_promote_charms.md) and [tag_charm_edge.yaml](release_charm_edge.md) should be used instead.
>
> Also, subject to **breaking changes on patch release**. `_promote_charm_legacy_1.yaml` is experimental & not part of the public interface.

## Limitations
Currently, this workflow can only be used on repositories that contain a single charm (that needs to be promoted; additional unreleased test charms are okay). That charm must be located at the root of the repository directory (i.e. `charmcraft.yaml` is present in the root of the repository)

## Usage
### Step 1: Add `promote.yaml` file to `.github/workflows/`
```yaml
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.
name: Promote charm

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
    name: Promote charm
    uses: canonical/data-platform-workflows/.github/workflows/_promote_charm_legacy_1.yaml@v0.0.0
    with:
      track: 'latest'
      from-risk: ${{ inputs.from-risk }}
      to-risk: ${{ inputs.to-risk }}
    secrets:
      charmhub-token: ${{ secrets.CHARMHUB_TOKEN_PROMOTION }}
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
      - edited
    branches:
      - main

jobs:
  check-pr:
    name: Check pull request
    uses: canonical/data-platform-workflows/.github/workflows/check_charm_pr.yaml@v0.0.0
    permissions: {}
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

### Step 4: Require approval for `stable` environment
Add the relevant team (e.g. canonical/data-postgresql) as a required reviewer before a workflow run with access to the `stable` GitHub environment can start: https://docs.github.com/en/actions/how-tos/deploy/configure-and-manage-deployments/control-deployments#using-required-reviews-in-workflows. This prevents an attacker who has compromised our workflows (e.g. via a supply chain attack) from (immediately) compromising our stable release artifacts.

### Step 5: Add Charmhub tokens
Add `CHARMHUB_TOKEN_PROMOTION` as an environment secret for the `beta` environment: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets#creating-secrets-for-an-environment. **Do not** add it as a repository secret.

`CHARMHUB_TOKEN_PROMOTION` generation (requires charmcraft >=4.4.0):
```
charmcraft login --quiet --charm foo --channel latest/beta --channel bar/beta --ttl 3600 --permission package-manage-releases --permission package-view-releases --export /dev/stdout
```
Replace:
- `foo` with charm name
- `latest` and `bar` with charm track(s)
- `3600` with expiration in seconds (that complies with https://library.canonical.com/corporate-policies/information-security-policies/secrets-management-policy)

Repeat the above steps, replacing `beta` with `candidate` in both the charmcraft command and in the GitHub environment name. Repeat again with `stable`. In total, generate 3 separate tokens.

### Step 6: Ensure metadata.yaml file is present
This workflow requires the charm directory (directory with charmcraft.yaml) to contain a metadata.yaml file with the `name` and `display-name` keys. For Kubernetes charms, all `oci-image` `resources` must be pinned to a sha256 digest. Syntax: https://juju.is/docs/sdk/metadata-yaml

"Unified charmcraft.yaml syntax" (where actions.yaml, charmcraft.yaml, config.yaml, and metadata.yaml are combined into a single charmcraft.yaml file) is not supported.

Rationale in [release_charm_edge.md](release_charm_edge.md#rationale)
