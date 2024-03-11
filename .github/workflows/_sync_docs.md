Workflow file: [_sync_docs.yaml](_sync_docs.yaml)

> [!WARNING]
> Subject to **breaking changes on patch release**. `_sync_docs.yaml` is experimental & not part of the public interface.

## Usage
Add `.yaml` file to `.github/workflows/`

```yaml
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.
name: Sync docs from Discourse

on:
  workflow_dispatch:
  schedule:
    - cron: # Refer to Run schedule below
  push:
    branches:
      - main

jobs:
  sync-docs:
    name: Sync docs from discourse
    uses: canonical/data-platform-workflows/.github/workflows/_sync_docs.yaml@v0.0.0
    secrets:
      discourse_api_username: ${{ secrets.DISCOURSE_API_USERNAME }}
      discourse_api_key: ${{ secrets.DISCOURSE_API_KEY }}
    permissions:
      contents: write  # Needed to login to Discourse
      pull-requests: write  # Needed to create PR
```

## Run schedule

|             repository            |   run time  |     cron      |
|:---------------------------------:|:-----------:|:-------------:|
| mysql-k8s-operator                | 12:10:00 AM | `10 00 * * *` |
| mysql-operator                    | 12:20:00 AM | `20 00 * * *` |
| postgresql-k8s-operator           | 12:30:00 AM | `30 00 * * *` |
| postgresql-operator               | 12:40:00 AM | `40 00 * * *` |
| mongodb-k8s-operator              | 12:50:00 AM | `50 00 * * *` |
| mongodb-operator                  |  1:00:00 AM | `00 01 * * *` |
| redis-k8s-operator                |  1:10:00 AM | `10 01 * * *` |
| redis-operator                    |  1:20:00 AM | `20 01 * * *` |
| opensearch-k8s-operator           |  1:30:00 AM | `30 01 * * *` |
| opensearch-operator               |  1:40:00 AM | `40 01 * * *` |
| kafka-k8s-operator                |  1:50:00 AM | `50 01 * * *` |
| kafka-operator                    |  2:00:00 AM | `00 02 * * *` |
| spark-history-server-k8s-operator |  2:10:00 AM | `10 02 * * *` |
| data-integrator                   |  2:20:00 AM | `20 02 * * *` |
| s3-integrator                     |  2:30:00 AM | `30 02 * * *` |
| data-platform-libs                |  2:40:00 AM | `40 02 * * *` |
| kafka-test-app                    |  2:50:00 AM | `50 02 * * *` |
| mysql-test-app                    |  3:00:00 AM | `00 03 * * *` |
| postgresql-test-app               |  3:10:00 AM | `10 03 * * *` |
| mysql-router-k8s-operator         |  3:20:00 AM | `20 03 * * *` |
| mysql-router-operator             |  3:30:00 AM | `30 03 * * *` |
| pgbouncer-k8s-operator            |  3:40:00 AM | `40 03 * * *` |
| pgbouncer-operator                |  3:50:00 AM | `50 03 * * *` |
| zookeeper-k8s-operator            |  4:00:00 AM | `00 04 * * *` |
| zookeeper-operator                |  4:10:00 AM | `10 04 * * *` |
| opensearch-dashboards-operator    |  4:20:00 AM | `20 04 * * *` |
| mongos-operator                   |  4:30:00 AM | `30 04 * * *` |
| spark-client-snap                 |  4:40:00 AM | `40 04 * * *` |