Workflow file: [release_charm_pr.yaml](release_charm_pr.yaml)

## Usage
### Step 1: Add `.yaml` file to `.github/workflows/`
```yaml
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.
on:
  pull_request:

jobs:
  build:
    name: Build charm
    uses: canonical/data-platform-workflows/.github/workflows/build_charm.yaml@v0.0.0
    permissions:
      contents: read

  release:
    name: Release charm to Charmhub branch
    needs:
      - build
    uses: canonical/data-platform-workflows/.github/workflows/release_charm_pr.yaml@v0.0.0
    with:
      track: 'latest'
      artifact-prefix: ${{ needs.build.outputs.artifact-prefix }}
    secrets:
      charmhub-token: ${{ secrets.CHARMHUB_TOKEN_EDGE_PR }}
    permissions:
      contents: read
```

### Step 2: Add Charmhub token
Add `CHARMHUB_TOKEN_EDGE_PR` as an environment secret for the `edge-pr` environment: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets#creating-secrets-for-an-environment. **Do not** add it as a repository secret.

`CHARMHUB_TOKEN_EDGE_PR` generation (requires charmcraft >=4.4.0):
```
charmcraft login --quiet --charm foo --channel latest/edge/pr-* --channel bar/edge/pr-* --ttl 3600 --permission package-manage-releases --permission package-manage-revisions --permission package-view-revisions --export /dev/stdout
```
Replace:
- `foo` with charm name
- `latest` and `bar` with charm track(s)
- `3600` with expiration in seconds (that complies with https://library.canonical.com/corporate-policies/information-security-policies/secrets-management-policy)

### Step 3: Ensure metadata.yaml file is present
This workflow requires the charm directory (directory with charmcraft.yaml) to contain a metadata.yaml file with the `name` key. If the charm uses OCI images (Kubernetes only), metadata.yaml must also contain the `resources` key. Syntax: https://juju.is/docs/sdk/metadata-yaml

"Unified charmcraft.yaml syntax" (where actions.yaml, charmcraft.yaml, config.yaml, and metadata.yaml are combined into a single charmcraft.yaml file) is not supported.

Rationale in [release_charm_edge.md](release_charm_edge.md#rationale)
