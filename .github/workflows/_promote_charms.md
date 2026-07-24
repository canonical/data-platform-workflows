Workflow file: [_promote_charms.yaml](_promote_charms.yaml)

> [!WARNING]
> Subject to **breaking changes on patch release**. `_promote_charms.yaml` is experimental & not part of the public interface.

## Limitations

- All charms must be released to the same track.
- (If using [charm-refresh](https://github.com/canonical/charm-refresh)) All charms must share an identical charm refresh compatibility version tag.

## Usage
### Step 1: Add `promote.yaml` file to `.github/workflows/`
```yaml
# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.
name: Promote charms by revision

on:
  workflow_dispatch:
    inputs:
      revisions:
        description: |
          Comma-separated list of git revision tags to promote.
          These must match the tags created by canonical/data-platform-workflows release_charm_edge.yaml

          Single-charm repo example: 'rev123,rev124'
          Monorepo example: 'mysql/rev123,mysql-k8s/rev124'
        required: true
        type: string
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
      revisions: ${{ inputs.revisions }}
      track: 'latest'
      to-risk: ${{ inputs.to-risk }}
    secrets:
      charmhub-token: ${{ secrets.CHARMHUB_TOKEN_PROMOTION }}
    permissions:
      contents: write  # Needed to edit GitHub releases
```

### Step 2: Add `check_pr.yaml` file to `.github/workflows/`
```yaml
# Copyright 2026 Canonical Ltd.
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
charmcraft login --quiet --charm foo --channel latest/beta --channel bar/beta --ttl 3600 --permission package-manage-releases --permission package-manage-revisions --permission package-view-revisions --export /dev/stdout
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
