Workflow file: [release_charm_pr.yaml](release_charm_pr.yaml)

## Usage
```yaml
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.
on:
  pull_request:

jobs:
  build:
    name: Build charm
    uses: canonical/data-platform-workflows/.github/workflows/build_charm.yaml@v0.0.0

  release:
    name: Release charm to Charmhub branch
    needs:
      - build
    uses: canonical/data-platform-workflows/.github/workflows/release_charm_pr.yaml@v0.0.0
    with:
      track: 'latest'
      artifact-prefix: ${{ needs.build.outputs.artifact-prefix }}
    secrets:
      charmhub-token: ${{ secrets.CHARMHUB_TOKEN }}
```
