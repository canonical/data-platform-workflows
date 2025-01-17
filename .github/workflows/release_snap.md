Workflow file: [release_snap.yaml](release_snap.yaml)

## Usage
Add `.yaml` file to `.github/workflows/`
```yaml
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.
name: Release to Snap Store

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

  release:
    name: Release snap
    needs:
      - build
    uses: canonical/data-platform-workflows/.github/workflows/release_snap.yaml@v0.0.0
    with:
      channel: latest/edge
      artifact-prefix: ${{ needs.build.outputs.artifact-prefix }}
    secrets:
      snap-store-token: ${{ secrets.SNAP_STORE_TOKEN }}
    permissions:
      contents: write  # Needed to create git tags
```

`SNAP_STORE_TOKEN` should be generated with `SNAPCRAFT_STORE_AUTH=candid` (e.g. `SNAPCRAFT_STORE_AUTH=candid snapcraft export-login`)
