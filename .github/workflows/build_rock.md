Workflow file: [build_rock.yaml](build_rock.yaml)

## Usage
```yaml
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.
jobs:
  build:
    name: Build rock
    uses: canonical/data-platform-workflows/.github/workflows/build_rock.yaml@v0.0.0
    permissions:
      actions: read  # Needed for GitHub API call to get workflow version
      contents: read
```

### Supported `platforms` syntax in rockcraft.yaml
Only "shorthand notation" is supported

Example rockcraft.yaml
```yaml
platforms:
  amd64:
  arm64:
```

`build-on` and `build-for` are not supported
