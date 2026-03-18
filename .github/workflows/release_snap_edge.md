Workflow file: [release_snap_edge.yaml](release_snap_edge.yaml)

## Usage
### Step 1: Add `release.yaml` file to `.github/workflows/`
```yaml
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.
name: Release to Snap Store edge

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

on:
  push:
    branches:
      - main

jobs:
  build:
    name: Build snap
    uses: canonical/data-platform-workflows/.github/workflows/build_snap.yaml@v0.0.0
    permissions:
      actions: read  # Needed for GitHub API call to get workflow version
      contents: read

  release:
    name: Release snap
    needs:
      - build
    uses: canonical/data-platform-workflows/.github/workflows/release_snap_edge.yaml@v0.0.0
    with:
      track: 'latest'
      artifact-prefix: ${{ needs.build.outputs.artifact-prefix }}
    secrets:
      snap-store-token: ${{ secrets.SNAP_STORE_TOKEN_EDGE }}
    permissions:
      actions: read  # Needed for GitHub API call to get workflow version
      contents: write  # Needed to create git tags
```

### Step 2: Add Snap Store token
Add `SNAP_STORE_TOKEN_EDGE` as an environment secret for the `edge` environment: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets#creating-secrets-for-an-environment. **Do not** add it as a repository secret.

`SNAP_STORE_TOKEN_EDGE` generation:
```
snapcraft export-login --snaps foo --channels latest/edge,foo/edge --expires 1970-01-01 -
```
Replace:
- `foo` with snap name
- `latest` and `foo` with snap track(s)
- `1970-01-01` with expiration date (that complies with https://library.canonical.com/corporate-policies/information-security-policies/secrets-management-policy)
