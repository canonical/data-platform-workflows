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
