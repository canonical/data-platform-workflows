Workflow file: [_update_bundle.yaml](_update_bundle.yaml)

> [!WARNING]
> Subject to **breaking changes on patch release**. `_update_bundle.yaml` is experimental & not part of the public interface.

## Usage
Add `.yaml` file to `.github/workflows/`
```yaml
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.
name: Update bundle

on:
  schedule:
    - cron: '53 0 * * *'  # Daily at 00:53 UTC

jobs:
  update-bundle:
    name: Update bundle
    uses: canonical/data-platform-workflows/.github/workflows/_update_bundle.yaml@v0.0.0
    with:
      path-to-bundle-file: bundle.yaml
      reviewers: canonical/data-platform-engineers,octocat
    secrets:
      token: ${{ secrets.CREATE_PR_APP_TOKEN }}
```
