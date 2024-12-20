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

If you use
```yaml
with:
  cache: true
```
remember to add your charm's branch(es) to charmcraftcache by running `ccc add` or by [opening an issue](https://github.com/canonical/charmcraftcache-hub/issues/new?assignees=&labels=add-charm&projects=&template=add_charm_branch.yaml&title=Add+charm+branch).

### Required charmcraft.yaml syntax
Only [ST124 - Multi-base platforms in craft tools](https://docs.google.com/document/d/1QVHxZumruKVZ3yJ2C74qWhvs-ye5I9S6avMBDHs2YcQ/edit) "shorthand notation" syntax is supported

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
