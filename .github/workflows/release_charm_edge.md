Workflow file: [release_charm_edge.yaml](release_charm_edge.yaml)

## Usage
### Step 1: Add `release.yaml` file to `.github/workflows/`

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
    permissions:
      contents: read

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
      charmhub-token: ${{ secrets.CHARMHUB_TOKEN_EDGE }}
    permissions:
      contents: write  # Needed to create git tags
```

### Step 2: Add Charmhub token
Add `CHARMHUB_TOKEN_EDGE` as an environment secret for the `edge` environment: https://docs.github.com/en/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets#creating-secrets-for-an-environment. **Do not** add it as a repository secret.

`CHARMHUB_TOKEN_EDGE` generation (requires charmcraft >=4.4.0):
```
charmcraft login --quiet --charm foo --channel latest/edge --channel bar/edge --ttl 3600 --permission package-manage-releases --permission package-manage-revisions --permission package-view-revisions --export /dev/stdout
```
Replace:
- `foo` with charm name
- `latest` and `bar` with charm track(s)
- `3600` with expiration in seconds (that complies with https://library.canonical.com/corporate-policies/information-security-policies/secrets-management-policy)

### Step 3: Ensure metadata.yaml file is present
This workflow requires the charm directory (directory with charmcraft.yaml) to contain a metadata.yaml file with the `name` key. If the charm uses OCI images (Kubernetes only), metadata.yaml must also contain the `resources` key. Syntax: https://juju.is/docs/sdk/metadata-yaml

"Unified charmcraft.yaml syntax" (where actions.yaml, charmcraft.yaml, config.yaml, and metadata.yaml are combined into a single charmcraft.yaml file) is not supported.

#### Rationale
It is simpler (for CI/CD tooling, developers, etc.) to have a consistent approach—either "unified charmcraft.yaml syntax" or separate files.

With "unified charmcraft.yaml syntax", charmcraft extracts the data back into actions.yaml, config.yaml, and metadata.yaml when packing the charm—but it removes comments from the YAML.

Benefits of separate files:
- no difference in files between source repository and *.charm artifact that would be confusing to developers
- comments in YAML files retained
- charmcraft just copies the files into the *.charm artifact, instead of using more complicated logic to extract that information (which would create more surface area for bugs)
