Workflow file: [update_bundle.yaml](update_bundle.yaml)

## Usage
Add `.yaml` file to `.github/workflows/`
```yaml
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
name: Update bundle

on:
  schedule:
    - cron: '53 0 * * *'  # Daily at 00:53 UTC

jobs:
  update-bundle:
    name: Update bundle
    uses: canonical/data-platform-workflows/.github/workflows/update_bundle.yaml@v2
    with:
      path-to-bundle-file: bundle.yaml
      reviewers: canonical/data-platform-engineers,octocat
    secrets:
      token: ${{ secrets.CREATE_PR_APP_TOKEN }}
```