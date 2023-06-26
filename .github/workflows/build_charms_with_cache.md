Workflow file: [build_charms_with_cache.yaml](build_charms_with_cache.yaml)

## Usage
```yaml
jobs:
 build:
    name: Build charms
    uses: canonical/data-platform-workflows/.github/workflows/build_charms_with_cache.yaml@<version>
    with:
      # Ubuntu version that will be used for running this job
      # It is used as value for "runs-on"
      ubuntu-version: ubuntu-20.04 
```
See https://discourse.charmhub.io/t/faster-integration-tests-with-github-caching/8782
