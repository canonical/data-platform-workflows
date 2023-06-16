Workflow file: [build_snap_without_cache.yaml](build_snap_without_cache.yaml)

## Usage
```yaml
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
jobs:
  build:
    name: Build snap
    uses: canonical/data-platform-workflows/.github/workflows/build_snap_without_cache.yaml@v2
```