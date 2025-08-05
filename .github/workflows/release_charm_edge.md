Workflow file: [release_charm_edge.yaml](release_charm_edge.yaml)

## Usage
Add `release.yaml` file to `.github/workflows/`

For charms that do not implement in-place upgrades & rollbacks with [charm-refresh](https://github.com/canonical/charm-refresh), the `tag` job should be omitted.
```yaml
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
name: Release to Charmhub edge

on:
  push:
    branches:
      - main

jobs:
  tag:
    name: Create charm refresh compatibility version git tag
    uses: canonical/data-platform-workflows/.github/workflows/tag_charm_edge.yaml@v0.0.0
    with:
      track: 'latest'
    permissions:
      contents: write  # Needed to create git tag
  
  build:
    name: Build charm
    needs:
      - tag
    uses: canonical/data-platform-workflows/.github/workflows/build_charm.yaml@v0.0.0

  release:
    name: Release charm
    needs:
      - tag
      - build
    uses: canonical/data-platform-workflows/.github/workflows/release_charm_edge.yaml@v0.0.0
    with:
      track: ${{ needs.tag.outputs.track }}
      artifact-prefix: ${{ needs.build.outputs.artifact-prefix }}
    secrets:
      charmhub-token: ${{ secrets.CHARMHUB_TOKEN }}
    permissions:
      contents: write  # Needed to create git tags
```
