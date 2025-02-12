Workflow file: static_code_analysis.yaml

## Usage

Add `static_code_analysis.yaml` file to `.github/workflows/`

```yaml
# Copyright 2025 Canonical Ltd.
# See LICENSE file for licensing details.
name: Static code static_code_analysis

on:
  schedule:
    - cron: "0 2 * * 6" # Every Saturday 2:00 AM UTC
  workflow_dispatch:

jobs:
  code_analysis:
    name: Tiobe Code Analysis
    uses: canonical/data-platform-workflows/.github/workflows/static_code_analysis.yaml@v0.0.0
    with:
      project: myprojectname
    secrets:
      tics_token: <TICS_TOKEN>
```

### `coverage.xml` file required

This job relies on unit tests (`tox -e unit`) generating a `coverage.xml` file in the root of the
repository. The `coverage.xml` file is used to generate a code coverage report on TICS.

### Schedule

The recommendation is to have a bi-weekly or (at most) weekly run of TICS.

