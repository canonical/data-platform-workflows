Workflow file: [lint_workflows.yaml](lint_workflows.yaml)

## Usage
```yaml
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
jobs:
  lint-workflows:
    name: Lint .github/workflows/
    uses: canonical/data-platform-workflows/.github/workflows/lint_workflows.yaml@v0.0.0
    permissions:
      contents: read
```
