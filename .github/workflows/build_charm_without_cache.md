Workflow file: [build_charm_without_cache.yaml](build_charm_without_cache.yaml)

## Usage
```yaml
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
jobs:
  build:
    name: Build charm
    uses: canonical/data-platform-workflows/.github/workflows/build_charm_without_cache.yaml@v2
```