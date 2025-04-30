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
      track: latest
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

### metadata.yaml required
This workflow requires the charm directory (directory with charmcraft.yaml) to contain a metadata.yaml file with the `name` key. If the charm uses OCI images (Kubernetes only), metadata.yaml must also contain the `resources` key. Syntax: https://juju.is/docs/sdk/metadata-yaml

"Unified charmcraft.yaml syntax" (where actions.yaml, charmcraft.yaml, config.yaml, and metadata.yaml are combined into a single charmcraft.yaml file) is not supported.

#### Rationale
It is simpler (for CI/CD tooling, developers, etc.) to have a consistent approach—either "unified charmcraft.yaml syntax" or separate files.

With "unified charmcraft.yaml syntax", charmcraft extracts the data back into actions.yaml, config.yaml, and metadata.yaml when packing the charm—but it removes comments from the YAML.

Benefits of separate files:
- no difference in files between source repository and *.charm artifact that would be confusing to developers
- comments in YAML files retained
- charmcraft just copies the files into the *.charm artifact, instead of using more complicated logic to extract that information (which would create more surface area for bugs)
