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

### metadata.yaml required
This workflow requires the charm directory (directory with charmcraft.yaml) to contain a metadata.yaml file with the `name` key. If the charm uses OCI images (Kubernetes only), metadata.yaml must also contain the `resources` key. Syntax: https://juju.is/docs/sdk/metadata-yaml

"Unified charmcraft.yaml syntax" (where actions.yaml, charmcraft.yaml, config.yaml, and metadata.yaml are combined into a single charmcraft.yaml file) is not supported.

Rationale in [release_charm_edge.md](release_charm_edge.md#rationale)
