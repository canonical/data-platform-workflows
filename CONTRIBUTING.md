## Versioning
The version number is automatically determined by [.github/workflows/__release.yaml](.github/workflows/__release.yaml)

This requires pull requests to be named according to the following convention.

(Note: There is one version for the entire repository—different workflows do not have different versions.)

### Public interface
*Public workflows*: workflows in [.github/workflows](.github/workflows) that do not begin with an underscore

The public interface consists of 
- (Explicit and implicit) input and output for the *public workflows*. This includes:
  - *Public workflow* file names
  - *Public workflow* `inputs` and `outputs` under `workflow_call`
  - Any assumptions made about the caller workflow repository layout (e.g. existence of tox.ini file). This applies to any workflows or scripts called by a *public workflow*, **even if they begin with an underscore**. (e.g. [_get_workflow_version.yaml](.github/workflows/_get_workflow_version.yaml), [python/cli](python/cli))
- [python/pytest_plugins/](python/pytest_plugins/)

### Pull request name convention
Pull request titles must begin with one of these prefixes:
- `breaking:` for breaking changes to the public interface
- `compatible:` for backwards-compatible changes to the public interface
- `patch:` if the public interface is not changed

Prefixes may contain an optional scope (e.g. `breaking(build_charm.yaml):`).
