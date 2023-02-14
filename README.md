[Reusable workflows](https://docs.github.com/en/actions/using-workflows/reusing-workflows) are located at [.github/workflows](.github/workflows)

Workflows that do **not** begin with an underscore (e.g. `foo.yaml`) may be called outside this repository.

Workflows that begin with one underscore (e.g. `_foo.yaml`) are internal and are only intended to be called by reusable workflows in this repository.

Workflows that begin with two underscores (e.g. `__foo.yaml`) are not reusable workflows. They are regular workflows for this repository.