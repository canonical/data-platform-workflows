Workflow file: [sync_docs.yaml](sync_docs.yaml)

## Usage
Add `.yaml` file to `.github/workflows/`

```yaml
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.
name: Sync Discourse docs

on:
  workflow_dispatch:
  schedule:
    - cron: '53 0 * * *'  # Daily at 00:53 UTC

jobs:
  sync-docs:
    name: Sync docs from Discourse
    uses: canonical/data-platform-workflows/.github/workflows/sync_docs.yaml@main
    permissions:
      contents: write  # Needed to push branch & tag
      pull-requests: write  # Needed to create PR
```
