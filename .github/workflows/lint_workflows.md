Workflow file: [lint_workflows.yaml](lint_workflows.yaml)

## Usage
### Step 1: Call lint_workflows.yaml
```yaml
# Copyright 2023 Canonical Ltd.
# See LICENSE file for licensing details.
jobs:
  lint-workflows:
    name: Lint .github/workflows/
    uses: canonical/data-platform-workflows/.github/workflows/lint_workflows.yaml@v0.0.0
    permissions:
      contents: read
```

### Step 2: Add `.github/zizmor.yaml` file
```yaml
rules:
  # Allowlist trusted actions
  forbidden-uses:
    config:
      # Actions in this list have remote code execution in our workflows. Even if the workflow has
      # limited permissions, those can be escaped. See https://github.com/AdnaneKhan/Cacheract and
      # "But Wait, There’s More" section of
      # https://www.praetorian.com/blog/codeqleaked-public-secrets-exposure-leads-to-supply-chain-attack-on-github-codeql/
      # In general, this list should be limited to organizations that we trust to have a baseline
      # level of operational security. Avoid adding actions that could be replaced with a few lines
      # of bash.
      allow:  # Get approval from your manager before adding actions to this list.
        - canonical/*
        - actions/*
        - docker/login-action
        - tiobe/tics-github-action
  # Pinning actions to a commit SHA has a security tradeoff—pinned actions cannot be later
  # compromised, but they also cannot be security patched.
  # Above (in `forbidden-uses`), we restrict actions usage to organizations that we trust to have
  # a baseline level of operational security.
  # Our actions usage involves several long-term support branches and reusable workflows (which
  # themselves use actions). For our threat model, we believe it is safer to limit actions usage to
  # organizations we trust and immediately receive security patching across our many branches than
  # it is to pin actions to a commit SHA.
  unpinned-uses:
    config:
      policies:
        canonical/*: ref-pin
        actions/*: ref-pin
        docker/login-action: ref-pin
        tiobe/tics-github-action: ref-pin
```
