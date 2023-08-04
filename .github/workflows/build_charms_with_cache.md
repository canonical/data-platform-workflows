Workflow file: [build_charms_with_cache.yaml](build_charms_with_cache.yaml)

## Usage
```yaml
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
jobs:
  build:
    name: Build charms
    uses: canonical/data-platform-workflows/.github/workflows/build_charms_with_cache.yaml@v0.0.0
    permissions:
      actions: write  # Needed to manage GitHub Actions cache
```
If any workflows call your workflow (i.e. your workflow includes `on: workflow_call`), recursively add
```yaml
permissions:
  actions: write  # Needed to manage GitHub Actions cache
```
to every calling workflow job.