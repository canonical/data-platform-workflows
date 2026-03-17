Workflow file: [release_snap_pr.yaml](release_snap_pr.yaml)

## Usage
Add `release.yaml` file to `.github/workflows/`
```yaml
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.
on:
  pull_request:

jobs:
  build:
    name: Build snap
    uses: canonical/data-platform-workflows/.github/workflows/build_snap.yaml@v0.0.0
    permissions:
      actions: read  # Needed for GitHub API call to get workflow version
      contents: read

  release:
    name: Release snap to Snap Store branch
    needs:
      - build
    uses: canonical/data-platform-workflows/.github/workflows/release_snap_pr.yaml@v0.0.0
    with:
      track: 'latest'
      artifact-prefix: ${{ needs.build.outputs.artifact-prefix }}
    secrets:
      snap-store-token: ${{ secrets.SNAP_STORE_TOKEN_EDGE_PR }}
    permissions:
      actions: read  # Needed for GitHub API call to get workflow version
      contents: read
```

Add `SNAP_STORE_TOKEN_EDGE_PR` as an environment secret for the `edge-pr` environment: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets#creating-secrets-for-an-environment

`SNAP_STORE_TOKEN_EDGE_PR` should be generated with `SNAPCRAFT_STORE_AUTH=candid`—e.g.:
```
SNAPCRAFT_STORE_AUTH=candid snapcraft export-login --snaps foo --channels latest/edge/pr-* --expires 1970-01-01 -
```
