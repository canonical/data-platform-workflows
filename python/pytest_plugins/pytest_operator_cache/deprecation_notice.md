# Deprecation notice

`pytest-operator-cache` is deprecated & will be removed in a future release

## Current behavior
With `pytest-operator-cache` installed, `ops_test.build_charm` (from [pytest-operator](https://github.com/charmed-kubernetes/pytest-operator)):
- On a local machine, builds the charm with charmcraft
- On CI (if `os.environ.get("CI") == "true"`), returns the path of an existing *.charm file—if the *.charm file was built on Ubuntu 22.04
    - (On CI, the *.charm files are built in a separate job [separate runner] from the integration tests)

## Migration instructions
In integration tests, instead of calling `ops_test.build_charm`, assume the *.charm file exists and fail the test if the *.charm file is missing. The charm should be built outside of the test

When running tests locally, if you would like the charm to be re-built each time the tests are run, consider using [charmcraftcache](https://github.com/canonical/charmcraftcache) (e.g. `ccc pack`) before the `pytest` command (e.g. in tox.ini). If you have multiple charms, `ccc pack` needs to be called once for each charm
