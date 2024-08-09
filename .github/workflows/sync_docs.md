Workflow file: [sync_docs.yaml](sync_docs.yaml)

## Usage
Add `.yaml` file to `.github/workflows/`

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
    permissions:
      contents: write  # Needed to push branch & tag
      pull-requests: write  # Needed to create PR
```

## Documentation requirements

Requirement: The overview topic must contain a navigation table with the columns "Level", "Path", and "Navlink"

Requirement: The navigation table of the overview page must be wrapped by the `[details]` HTML/markdown element as follows:

```
# Navigation

[details=Navigation]

<navigation table goes here>

[/details]

```

> [!NOTE]  
> There should be a white space before and after the `[details]` and `[/details]` lines. Otherwise, Discourse/Charmhub may not parse them correctly.

Requirement: Links in the `Navlink` column must be formatted as `[Text](/t/<number>)`. 

They **must not** be formatted as `[Text](/t/<some-additional-slug-text>/<number>)`.

### Examples
The following documentation sets fulfill the above requirements and have been tested:
* [PostgreSQL VM](https://discourse.charmhub.io/t/charmed-postgresql-documentation/9710)
* [PostgreSQL K8s](https://discourse.charmhub.io/t/charmed-postgresql-k8s-documentation/9307)
* [PgBouncer VM](https://discourse.charmhub.io/t/pgbouncer-documentation/12133)
* [PgBouncer K8s](https://discourse.charmhub.io/t/pgbouncer-k8s-documentation/12132)
* [MySQL Router K8s](https://discourse.charmhub.io/t/mysql-router-k8s-documentation/12130)
