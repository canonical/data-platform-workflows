Workflow file: [sync_issue_to_jira.yaml](sync_issue_to_jira.yaml)

## Usage
Add `.yaml` file to `.github/workflows/`
```yaml
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
name: Sync issue to Jira

on:
  issues:
    types: [opened, reopened, closed]

jobs:
  sync:
    name: Sync GitHub issue to Jira
    uses: canonical/data-platform-workflows/.github/workflows/sync_issue_to_jira.yaml@v2
    with:
      jira-base-url: https://warthogs.atlassian.net
      jira-project-key: DPE
      jira-component-names: mysql-k8s,mysql-router-k8s
    secrets:
      jira-api-token: ${{ secrets.JIRA_API_TOKEN }}
      jira-user-email: ${{ secrets.JIRA_USER_EMAIL }}
    permissions:
      issues: write  # Needed to create issue comment
```