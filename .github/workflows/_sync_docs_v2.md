Workflow file: [_sync_docs_v2.yaml](_sync_docs_v2.yaml)

> [!WARNING]
> Subject to **breaking changes on patch release**. `_sync_docs_v2.yaml` is experimental & not part of the public interface.

## Usage
Add `.yaml` file to `.github/workflows/`

```yaml
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.
name: Sync Discourse docs (v2)

on:
  workflow_dispatch:
  schedule:
    - cron: '53 0 * * *'  # Daily at 00:53 UTC

jobs:
  sync-docs-v2:
    name: Sync docs from Discourse (v2)
    uses: canonical/data-platform-workflows/.github/workflows/_sync_docs_2.yaml@main
    permissions:
      contents: write  # Needed to push branch & tag
      pull-requests: write  # Needed to create PR
```
