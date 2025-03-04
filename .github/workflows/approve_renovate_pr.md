Workflow file: [approve_renovate_pr.yaml](approve_renovate_pr.yaml)

## Usage
Add `approve_renovate_pr.yaml` file to `.github/workflows/`

```yaml
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.
name: Approve Renovate pull request

on:
  pull_request:
    types:
      - opened

jobs:
  approve-pr:
    name: Approve Renovate pull request
    uses: canonical/data-platform-workflows/.github/workflows/approve_renovate_pr.yaml@v0.0.0
    permissions:
      pull-requests: write  # Needed to approve PR
```
