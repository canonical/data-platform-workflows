Workflow file: [update_bundle_snaps.yaml](update_bundle_snaps.yaml)

## Usage
Add `.yaml` file to `.github/workflows/`
```yaml
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
name: Update bundle snaps

on:
  schedule:
    - cron: '53 0 * * *'  # Daily at 00:53 UTC

jobs:
  update-bundle-snaps:
    name: Update bundle snaps
    uses: canonical/data-platform-workflows/.github/workflows/update_bundle_snaps.yaml@v0.0.0
    with:
      path-to-snaps-file: snaps.yaml
      path-to-bundle-file: bundle.yaml
      reviewers: canonical/data-platform-engineers,octocat
    secrets:
      token: ${{ secrets.CREATE_PR_APP_TOKEN }}
```