Workflow file: [_promote_snaps.yaml](_promote_snaps.yaml)

> [!WARNING]
> Subject to **breaking changes on patch release**. `_promote_snaps.yaml` is experimental & not part of the public interface.

## Usage
### Step 1: Add `promote.yaml` file to `.github/workflows/`
```yaml
# Copyright 2026 Canonical Ltd.
# See LICENSE file for licensing details.
name: Promote snaps

on:
  workflow_dispatch:
    inputs:
      from-risk:
        description: Promote from this Snapcraft risk
        required: true
        type: choice
        options:
          - edge
          - beta
          - candidate
      to-risk:
        description: Promote to this Snapcraft risk
        required: true
        type: choice
        options:
          - beta
          - candidate
          - stable

jobs:
  promote:
    name: Promote snaps
    uses: canonical/data-platform-workflows/.github/workflows/_promote_snaps.yaml@v0.0.0
    with:
      track: 'latest'
      from-risk: ${{ inputs.from-risk }}
      to-risk: ${{ inputs.to-risk }}
    secrets:
      snapcraft-token: ${{ secrets.SNAPCRAFT_TOKEN }}
    permissions:
      contents: write  # Needed to edit GitHub releases
```

### Step 2: Add `.github/release.yaml` file
```yaml
changelog:
  categories:
    - title: Features
      labels:
        - enhancement
    - title: Bug fixes
      labels:
        - bug
```

### Step 3: Ensure snapcraft.yaml file is present
This workflow requires the snap directory to contain a snapcraft.yaml file with the `name` key.
