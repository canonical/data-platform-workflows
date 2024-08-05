Workflow file: [_sync_docs_v2.yaml](_sync_docs_v2.yaml)

> [!WARNING]
> Subject to **breaking changes on patch release**. `_sync_docs_v2.yaml` is experimental & not part of the public interface.

## Usage
Add `.yaml` file to `.github/workflows/`

```yaml
# Copyright 2024 Canonical Ltd.
# See LICENSE file for licensing details.
name: Sync Discourse docs (v2)

on:
  workflow_dispatch:
  schedule:
    - cron: # Refer to Run schedule below

jobs:
  sync-docs-v2:
    name: Sync docs from Discourse (v2)
    uses: canonical/data-platform-workflows/.github/workflows/_sync_docs_2.yaml@main
    permissions:
      contents: write  # Needed to push branch & tag
      pull-requests: write  # Needed to create PR
```

## Run schedule

Cron job schedules for Data Platform repositories

### SQL
| repository                | run time | cron          |
|:-------------------------:|:--------:|:-------------:|
| mysql-k8s-operator        | 12:00 AM | `00 00 * * *` |
| mysql-operator            | 12:10 AM | `10 00 * * *` |
| mysql-test-app            | 12:20 AM | `20 00 * * *` |
| mysql-router-k8s-operator | 12:30 AM | `30 00 * * *` |
| mysql-router-operator     | 12:40 AM | `40 00 * * *` |
| postgresql-k8s-operator   | 12:50 AM | `50 00 * * *` |
| postgresql-operator       | 01:00 AM | `00 01 * * *` |
| postgresql-test-app       | 01:10 AM | `10 01 * * *` |
| pgbouncer-k8s-operator    | 01:20 AM | `20 01 * * *` |
| pgbouncer-operator        | 01:30 AM | `30 01 * * *` |

### NoSQL
| repository                     | run time | cron          |
|:------------------------------:|:--------:|:-------------:|
| mongodb-k8s-operator           | 01:40 AM | `40 01 * * *` |
| mongodb-operator               | 01:50 AM | `50 01 * * *` |
| mongos-operator                | 02:00 AM | `00 02 * * *` |
| opensearch-k8s-operator        | 02:10 AM | `10 02 * * *` |
| opensearch-operator            | 02:20 AM | `20 02 * * *` |
| opensearch-dashboards-operator | 02:30 AM | `30 02 * * *` |
| redis-k8s-operator             | 02:40 AM | `40 02 * * *` |
| redis-operator                 | 02:50 AM | `50 02 * * *` |

### Big Data
| repository                        | run time | cron          |
|:---------------------------------:|:--------:|:-------------:|
| kafka-k8s-operator                | 03:00 AM | `00 03 * * *` |
| kafka-operator                    | 03:10 AM | `10 03 * * *` |
| kafka-test-app                    | 03:20 AM | `20 03 * * *` |
| zookeeper-k8s-operator            | 03:30 AM | `30 03 * * *` |
| zookeeper-operator                | 03:40 AM | `40 03 * * *` |
| spark-history-server-k8s-operator | 03:50 AM | `50 03 * * *` |
| spark-client-snap                 | 04:00 AM | `00 04 * * *` |

### Other
| repository         | run time | cron          |
|:------------------:|:--------:|:-------------:|
| data-integrator    | 04:10 AM | `10 04 * * *` |
| s3-integrator      | 04:20 AM | `20 04 * * *` |
| data-platform-libs | 04:30 AM | `30 04 * * *` |
