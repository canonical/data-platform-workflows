Workflow file: [build_charm.yaml](build_charm.yaml)

## Usage
```yaml
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
jobs:
  build:
    name: Build charm
    uses: canonical/data-platform-workflows/.github/workflows/build_charm.yaml@v0.0.0
```

Unless you disable caching (with `cache: false`), remember to add your charm's branch(es) to charmcraftcache: https://github.com/canonical/charmcraftcache?tab=readme-ov-file#usage

### Required charmcraft.yaml syntax
Only ["multi-base shorthand notation" syntax](https://canonical-charmcraft.readthedocs-hosted.com/en/stable/reference/platforms/#multi-base-shorthand-notation) is supported

#### Example
```yaml
platforms:
  ubuntu@22.04:amd64:
  ubuntu@22.04:arm64:
  ubuntu@24.04:amd64:
  ubuntu@24.04:arm64:
```

Under the charmcraft.yaml `platforms` key, `build-on` and `build-for` syntax are not supported

The `base` and `bases` charmcraft.yaml keys are not supported
