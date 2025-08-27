Workflow file: [_mirror_charm.yaml](_mirror_charm.yaml)

> [!WARNING]
> Subject to **breaking changes on patch release**. `_mirror_charm.yaml` is experimental & not part of the public interface.

## Usage
Add `mirror` job to `.github/workflows/release.yaml`. See [release_charm_edge.md](release_charm_edge.md) for the other contents of `release.yaml`

```yaml
jobs:
  # [...]
  
  mirror:
    strategy:
      matrix:
        charm:
          - path: kubernetes
            repo: canonical/mysql-router-k8s-operator-mirror
          - path: machines
            repo: canonical/mysql-router-operator-mirror
    name: Mirror charm | ${{ matrix.charm.path }}
    needs:
      - release
    uses: canonical/data-platform-workflows/.github/workflows/_mirror_charm.yaml@v0.0.0
    with:
      path-to-charm-directory: ${{ matrix.charm.path }}
      repository: ${{ matrix.charm.repo }}
    secrets:
      token: ${{ secrets.MIRROR_REPOS_PAT }}
```

### metadata.yaml required
This workflow requires the charm directory (directory with charmcraft.yaml) to contain a metadata.yaml file with the `name` key.

"Unified charmcraft.yaml syntax" (where actions.yaml, charmcraft.yaml, config.yaml, and metadata.yaml are combined into a single charmcraft.yaml file) is not supported.

Rationale in [release_charm_edge.md](release_charm_edge.md#rationale)
