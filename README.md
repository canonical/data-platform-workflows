## Usage

[Reusable workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows) are located at [.github/workflows](.github/workflows)

Workflows that do **not** begin with an underscore (e.g. `foo.yaml`) may be called outside this repository.

Workflows that begin with one underscore (e.g. `_foo.yaml`) are internal and are only intended to be called by reusable workflows in this repository (that begin with zero or one underscores).

Workflows that begin with two underscores (e.g. `__foo.yaml`) are for this repository only. They may only be (triggered by an event on this repository or) called by workflows in this repository that begin with two underscores.

### Version

Recommendation: pin to the latest major version.

For example:
```yaml
jobs:
  build:
    name: Build charms
    uses: canonical/data-platform-workflows/.github/workflows/build_charms_with_cache.yaml@v1
```

Update when a new major version is available—after a new major version is released, bug fixes will **not** be backported to old major versions.

Note: all workflows in this repository share a version number. If a breaking change is made to the public interface of one workflow, all workflows will have a new major version even if they have no breaking changes.

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md)