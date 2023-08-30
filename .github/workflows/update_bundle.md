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
    uses: canonical/data-platform-workflows/.github/workflows/update_bundle.yaml@v0.0.0
    with:
      path-to-bundle-file: bundle.yaml
      reviewers: canonical/data-platform-engineers,octocat
      include: app1       # If include is not provided, all apps will be updated
      exclude: app3,app4  # Except those provided in the exclude option. 
    secrets:
      token: ${{ secrets.CREATE_PR_APP_TOKEN }}
```