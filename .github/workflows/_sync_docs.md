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
    name: Sync docs from Discourse
    uses: canonical/data-platform-workflows/.github/workflows/_sync_docs.yaml@v0.0.0
    secrets:
      discourse_api_username: ${{ secrets.DISCOURSE_API_USERNAME }}
      discourse_api_key: ${{ secrets.DISCOURSE_API_KEY }}
    permissions:
      contents: write  # Needed to create commits with Discourse content and update tags
      pull-requests: write  # Needed to create PR
```

## Run schedule
### SQL
| repository                | run time | cron          |
|:-------------------------:|:--------:|:-------------:|
| mysql-k8s-operator        | 12:10 AM | `10 00 * * *` |
| mysql-operator            | 12:20 AM | `20 00 * * *` |
| mysql-test-app            | 3:00 AM  | `00 03 * * *` |
| mysql-router-k8s-operator | 3:20 AM  | `20 03 * * *` |
| mysql-router-operator     | 3:30 AM  | `30 03 * * *` |
| postgresql-k8s-operator   | 12:30 AM | `30 00 * * *` |
| postgresql-operator       | 12:40 AM | `40 00 * * *` |
| postgresql-test-app       | 3:10 AM  | `10 03 * * *` |
| pgbouncer-k8s-operator    | 3:40 AM  | `40 03 * * *` |
| pgbouncer-operator        | 3:50 AM  | `50 03 * * *` |

### NoSQL
| repository                     | run time | cron          |
|:------------------------------:|:--------:|:-------------:|
| mongodb-k8s-operator           | 12:50 AM | `50 00 * * *` |
| mongodb-operator               | 1:00 AM  | `00 01 * * *` |
| mongos-operator                | 4:30 AM  | `30 04 * * *` |
| opensearch-k8s-operator        | 1:30 AM  | `30 01 * * *` |
| opensearch-operator            | 1:40 AM  | `40 01 * * *` |
| opensearch-dashboards-operator | 4:20 AM  | `20 04 * * *` |
| redis-k8s-operator             | 1:10 AM  | `10 01 * * *` |
| redis-operator                 | 1:20 AM  | `20 01 * * *` |

### Big Data
| repository                        | run time | cron          |
|:---------------------------------:|:--------:|:-------------:|
| kafka-k8s-operator                | 1:50 AM  | `50 01 * * *` |
| kafka-operator                    | 2:00 AM  | `00 02 * * *` |
| kafka-test-app                    | 2:50 AM  | `50 02 * * *` |
| zookeeper-k8s-operator            | 4:00 AM  | `00 04 * * *` |
| zookeeper-operator                | 4:10 AM  | `10 04 * * *` |
| spark-history-server-k8s-operator | 2:10 AM  | `10 02 * * *` |
| spark-client-snap                 | 4:40 AM  | `40 04 * * *` |

### Other
| repository         | run time | cron          |
|:------------------:|:--------:|:-------------:|
| data-integrator    | 2:20 AM  | `20 02 * * *` |
| s3-integrator      | 2:30 AM  | `30 02 * * *` |
| data-platform-libs | 2:40 AM  | `40 02 * * *` |