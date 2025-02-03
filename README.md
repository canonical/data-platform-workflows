## Usage
### Workflows
| Name                                                                       | Description                                                                |
|----------------------------------------------------------------------------|----------------------------------------------------------------------------|
| [lint.yaml](.github/workflows/lint.md)                                     | Lint GitHub Actions workflows (`.github/workflows/`) and `tox run -e lint` |
| [integration_test_charm.yaml](.github/workflows/integration_test_charm.md) | Integration test charm                                                     |
| [build_snap.yaml](.github/workflows/build_snap.md)                         | Build snap                                                                 |
| [build_rock.yaml](.github/workflows/build_rock.md)                         | Build rock                                                                 |
| [build_charm.yaml](.github/workflows/build_charm.md)                       | Build charm                                                                |
| [release_snap.yaml](.github/workflows/release_snap.md)                     | Release snap to Snap Store                                                 |
| [release_rock.yaml](.github/workflows/release_rock.md)                     | Release rock to GitHub Container Registry                                  |
| [release_charm.yaml](.github/workflows/release_charm.md)                   | Release charm to Charmhub                                                  |
| [promote_charm.yaml](.github/workflows/promote_charm.md)                   | `charmcraft promote`, update git tags, & generate release notes            |
| [check_charm_pr.yaml](.github/workflows/check_charm_pr.md)                 | Check charm pull request has required labels for release notes             |
| [sync_docs.yaml](.github/workflows/sync_docs.md)                           | Sync Discourse documentation to GitHub                                     |
| [_update_bundle.yaml](.github/workflows/_update_bundle.md)                 | **Experimental** Update charm revisions in bundle                          |

### Version
Recommendation: pin the latest version (e.g. `v1.0.0`) and use [Renovate](https://docs.renovatebot.com/) to stay up-to-date.

Bug fixes will **not** be backported.

Example workflow:
```yaml
jobs:
  build:
    name: Build charms
    uses: canonical/data-platform-workflows/.github/workflows/build_charm.yaml@v1.0.0
```

Example Renovate configuration:
```json5
{
  "enabledManagers": ["poetry", "github-actions"],
  "packageRules": [
    // Later rules override earlier rules

    // Group data-platform-workflows Python package & workflow updates into the same PR
    {
      "matchManagers": ["poetry"],
      "matchPackageNames": ["canonical/data-platform-workflows"],
      // Ensure Renovate prefers vX.0.0 tag (e.g. "v24.0.0") over vX tag (e.g. "v24") if vX.X.X tag
      // currently in use
      // (Matches default versioning of "github-actions" manager)
      "versioning": "docker",
      "groupName": "data-platform-workflows"
    },
    {
      "matchManagers": ["github-actions"],
      "matchPackageNames": ["canonical/data-platform-workflows"],
      "groupName": "data-platform-workflows"
    },
  ]
}

```

Note: all workflows in this repository share a version number. If a breaking change is made to the public interface of one workflow, all workflows will have a new major version even if they have no breaking changes.

If you do not want to use Renovate, pin to the latest major version (e.g. `v1`).

### Public interface
Workflows that do **not** begin with an underscore (e.g. `foo.yaml`) may be called outside this repository.

Workflows that begin with one underscore (e.g. `_foo.yaml`) are internal and are only intended to be called by reusable workflows in this repository (that begin with zero or one underscores).

Workflows that begin with two underscores (e.g. `__foo.yaml`) are for this repository only. They may only be (triggered by an event on this repository or) called by workflows in this repository that begin with two underscores.

## Contributing
See [CONTRIBUTING.md](CONTRIBUTING.md)
