Workflow file: [build_snap.yaml](build_snap.yaml)

## Usage
```yaml
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.
jobs:
  build:
    name: Build snap
    uses: canonical/data-platform-workflows/.github/workflows/build_snap.yaml@v0.0.0
```

### Supported `platforms` and `architectures` syntax in snapcraft.yaml
See https://snapcraft.io/docs/architectures#how-to-create-a-snap-for-a-specific-architecture

#### core24
Only `platforms` is supported. `architectures` is not supported

Only "shorthand notation" is supported

Example snapcraft.yaml
```yaml
platforms:
  amd64:
  arm64:
```

`build-on` and `build-for` are not supported

#### core22
Only `architectures` is supported. `platforms` is not supported

`architectures` must be a list of dictionaries. Each dictionary in the list must contain a `build-on` key

Example snapcraft.yaml
```yaml
architectures:
  - build-on: [amd64]
    build-for: [amd64]
  - build-on: [arm64]
    build-for: [arm64]
```
