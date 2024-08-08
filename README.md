## Usage
### Workflows
| Name                                                                       | Description                                                                 |
|----------------------------------------------------------------------------|-----------------------------------------------------------------------------|
| [lint.yaml](.github/workflows/lint.md)                                     | Lint GitHub Actions workflows (`.github/workflows/`) and `tox run -e lint`  |
| [integration_test_charm.yaml](.github/workflows/integration_test_charm.md) | Integration test charm                                                      |
| [build_snap.yaml](.github/workflows/build_snap.md)                         | Build snap                                                                  |
| [build_rock.yaml](.github/workflows/build_rock.md)                         | Build rock                                                                  |
| [build_charm.yaml](.github/workflows/build_charm.md)                       | Build charm                                                                 |
| [release_snap.yaml](.github/workflows/release_snap.md)                     | Release snap to Snap Store                                                  |
| [release_rock.yaml](.github/workflows/release_rock.md)                     | Release rock to GitHub Container Registry                                   |
| [release_charm.yaml](.github/workflows/release_charm.md)                   | Release charm to Charmhub                                                   |
| [update_bundle.yaml](.github/workflows/update_bundle.md)                   | Update charm revisions in bundle                                            |
| [sync_issue_to_jira.yaml](.github/workflows/sync_issue_to_jira.md)         | Sync GitHub issues to Jira issues                                           |
| [sync_docs.yaml](.github/workflows/sync_docs.md)                           | Sync Discourse documentation to GitHub (custom script)                      |

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
      // Workaround for https://github.com/renovatebot/renovate/discussions/23628
      "versioning": "semver",
      "groupName": "data-platform-workflows",
      // Workaround: data-platform-workflows Python packages use git tags instead of pyproject.toml
      // for versioning. Therefore, Renovate will always think an update is a major version update.
      "separateMajorMinor": false
    },
    {
      "matchManagers": ["github-actions"],
      "matchPackageNames": ["canonical/data-platform-workflows"],
      "groupName": "data-platform-workflows",
      // Workaround: data-platform-workflows Python packages use git tags instead of pyproject.toml
      // for versioning. Therefore, Renovate will always think an update is a major version update.
      // Since we want packages to be updated alongside workflows (actions), we must disable
      // separate major PRs for workflows as well.
      "separateMajorMinor": false
    }
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