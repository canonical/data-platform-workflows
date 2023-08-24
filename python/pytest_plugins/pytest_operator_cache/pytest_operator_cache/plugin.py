import os
import pathlib

import yaml


def pytest_configure(config):
    if os.environ.get("CI") == "true":
        # Running in GitHub Actions; skip build step
        plugin = config.pluginmanager.get_plugin("pytest-operator")
        plugin.OpsTest.build_charm = build_charm

        # Remove charmcraft dependency from `ops_test` fixture
        check_deps = plugin.check_deps
        plugin.check_deps = lambda *deps: check_deps(
            *(dep for dep in deps if dep != "charmcraft")
        )


async def build_charm(
    self, charm_path: str | os.PathLike, bases_index: int = None
) -> pathlib.Path:
    charm_path = pathlib.Path(charm_path)
    if bases_index is not None:
        charmcraft_yaml = yaml.safe_load((charm_path / "charmcraft.yaml").read_text())
        assert charmcraft_yaml["type"] == "charm"
        base = charmcraft_yaml["bases"][bases_index]
        # Handle multiple base formats
        # See https://discourse.charmhub.io/t/charmcraft-bases-provider-support/4713
        version = base.get("build-on", [base])[0]["channel"]
        packed_charms = list(charm_path.glob(f"*{version}-amd64.charm"))
    else:
        packed_charms = list(charm_path.glob("*.charm"))
    if len(packed_charms) == 1:
        # python-libjuju's model.deploy(), juju deploy, and juju bundle files expect local charms
        # to begin with `./` or `/` to distinguish them from Charmhub charms.
        # Therefore, we need to return an absolute path—a relative `pathlib.Path` does not start
        # with `./` when cast to a str.
        # (python-libjuju model.deploy() expects a str but will cast any input to a str as a
        # workaround for pytest-operator's non-compliant `build_charm` return type of
        # `pathlib.Path`.)
        return packed_charms[0].resolve(strict=True)
    elif len(packed_charms) > 1:
        message = f"More than one matching .charm file found at {charm_path=}: {packed_charms}."
        if bases_index is None:
            message += " Specify `bases_index`"
        else:
            message += " Does charmcraft.yaml contain non-amd64 architecture?"
        raise ValueError(message)
    else:
        raise ValueError(
            f"Unable to find amd64 .charm file for {bases_index=} at {charm_path=}"
        )
