Workflow file: [release_charm.yaml](release_charm.yaml)

## Usage
Add `.yaml` file to `.github/workflows/`
```yaml
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
name: Release to Charmhub

on:
  push:
    branches:
      - main

jobs:
  build:
    name: Build charm
    uses: canonical/data-platform-workflows/.github/workflows/build_charm_without_cache.yaml@v2

  release:
    name: Release charm
    needs:
      - build
    uses: canonical/data-platform-workflows/.github/workflows/release_charm.yaml@v2
    with:
      channel: latest/edge
      artifact-name: ${{ needs.build.outputs.artifact-name }}
    secrets:
      charmhub-token: ${{ secrets.CHARMHUB_TOKEN }}
    permissions:
      contents: write  # Needed to create GitHub release
```