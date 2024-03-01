Workflow file: [release_rock.yaml](release_rock.yaml)

## Usage
Add `.yaml` file to `.github/workflows/`
```yaml
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.
name: Release to GitHub Container Registry

concurrency:
  group: ${{ github.workflow }}-${{ github.ref }}
  cancel-in-progress: true

on:
  push:
    branches:
      - main

jobs:
  build:
    name: Build rock
    uses: canonical/data-platform-workflows/.github/workflows/build_rock.yaml@v0.0.0

  release:
    name: Release rock
    needs:
      - build
    uses: canonical/data-platform-workflows/.github/workflows/release_rock.yaml@v0.0.0
    with:
      artifact-prefix: ${{ needs.build.outputs.artifact-prefix }}
    permissions:
      packages: write  # Needed to publish to GitHub Container Registry
```

Grant package `Write` role to GitHub Actions for the source GitHub repository: https://docs.github.com/en/packages/learn-github-packages/configuring-a-packages-access-control-and-visibility#ensuring-workflow-access-to-your-package
