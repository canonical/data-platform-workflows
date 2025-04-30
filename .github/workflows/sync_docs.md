Workflow file: [sync_docs.yaml](sync_docs.yaml)

## Usage
Add `sync_docs.yaml` file to `.github/workflows/`

```yaml
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.
name: Sync Discourse docs

on:
  workflow_dispatch:
  schedule:
    - cron: '53 0 * * *'  # Daily at 00:53 UTC

jobs:
  sync-docs:
    name: Sync docs from Discourse
    uses: canonical/data-platform-workflows/.github/workflows/sync_docs.yaml@v0.0.0
    with:
      reviewers: canonical/data-platform-technical-authors,octocat
    permissions:
      contents: write  # Needed to push branch & tag
      pull-requests: write  # Needed to create PR
```

### metadata.yaml required
This workflow requires the charm directory (directory with charmcraft.yaml) to contain a metadata.yaml file with the `docs` key. Syntax: https://juju.is/docs/sdk/metadata-yaml

"Unified charmcraft.yaml syntax" (where actions.yaml, charmcraft.yaml, config.yaml, and metadata.yaml are combined into a single charmcraft.yaml file) is not supported.

Rationale in [release_charm_edge.md](release_charm_edge.md#rationale)

## Behavior

Downloads all Discourse topics in the charm's Charmhub documentation to `/docs/` directory in the charm's repository.

>[!NOTE]
> Any content in the `/docs/` directory that is not part of this workflow will get removed.

The topics are determined by the navigation table in the charm's overview page - i.e. the page linked in the `metadata.yaml` `docs:` field. 

When the workflow is triggered, it downloads all Discourse topics in their latest state and compares them to the `/docs/` directory in the default branch (e.g. `main`).
* If the contents match, GitHub is up to date with Discourse. Nothing happens.
* If the contents do not match, Discourse is ahead of GitHub. The workflow opens or updates a PR for the `sync-docs` branch with the diff between Discourse and GitHub.

Each Discourse topic is downloaded to either: `/docs/`, `/docs/tutorial/`, `/docs/how-to/`, `/docs/reference/`, or `/docs/explanation/` depending on their slug prefix. Sub-categories will not create an additional directory.

```
# Example navtable:

| Level |      Path      |          Navlink          |
|-------|----------------|---------------------------|
|   1   | t-landing      | [Tutorial](/t/123)        |
|   2   | t-introduction | [Introduction](/t/124)    |
|   1   | h-landing      | [How To]()                |
|   2   | h-set-up       | [Set up](/t/125)          |
|   3   | h-deploy-lxd   | [Deploy on LXD](/t/126)   |
|   2   | h-monitoring   | [Monitoring]()            |
|   3   | h-alert        | [Add alert rules](/t/127) |

# Expected /docs output:

/docs/overview.md
/docs/tutorial/t-landing.md
/docs/tutorial/t-introduction.md
/docs/how-to/h-set-up.md
/docs/how-to/h-deploy-lxd.md
/docs/how-to/h-alert.md
```

## Documentation requirements

**Requirement**: The overview topic must contain a navigation table with the columns "Level", "Path", and "Navlink"

**Requirement**: The navigation table of the overview topic must be wrapped by the `[details]` HTML/markdown element as follows:

```
# Navigation

[details=Navigation]

<navigation table goes here>

[/details]

```

> [!NOTE]  
> Make sure to leave a white space before and after the `[details]` and `[/details]` lines. Otherwise, Discourse/Charmhub may not parse them correctly.

**Requirement**: Links to topics in the `Navlink` column must be formatted as `[Text](/t/<topic_id>)`. 

They **must not** be formatted as `[Text](/t/<some-additional-slug-text>/<topic_id>)`.

### Examples
The following documentation sets fulfill the above requirements and have been tested:
* [PostgreSQL VM](https://discourse.charmhub.io/t/charmed-postgresql-documentation/9710)
* [PostgreSQL K8s](https://discourse.charmhub.io/t/charmed-postgresql-k8s-documentation/9307)
* [PgBouncer VM](https://discourse.charmhub.io/t/pgbouncer-documentation/12133)
* [PgBouncer K8s](https://discourse.charmhub.io/t/pgbouncer-k8s-documentation/12132)
* [MySQL Router K8s](https://discourse.charmhub.io/t/mysql-router-k8s-documentation/12130)
