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
Only [ST124 - Multi-base platforms in craft tools](https://docs.google.com/document/d/1QVHxZumruKVZ3yJ2C74qWhvs-ye5I9S6avMBDHs2YcQ/edit) "shorthand notation" syntax is supported in charmcraft.yaml

Follow [step #1 from charmcraftst124's documentation](https://github.com/canonical/charmcraftst124?tab=readme-ov-file#step-1-update-charmcraftyaml-to-supported-syntax)
