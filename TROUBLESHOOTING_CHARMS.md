Whenever a test fails, data-platform-workflows will capture that run logs using [sosreport](https://github.com/sosreport/sos).

The logs can be downloaded from the run's "Summary" page.

The sosreport is ran in the actual runner and captures logs from the host itself as well as the model's containers (LXC / k8s).

# Log structure

```
/
|
+---- juju-debug-log.txt: captured at the end of the run
|
+---- juju-status.txt: captured at the end of the run
|
+---- sos-collector-...
|
+---- sosreport-...
```

## Github Runner logs

The tarball `sosreport-` contains all the host logs. It will hold its syslog, journal and kernel logs.

Relevant logs:
* /var/log/{kern,syslog}.log: OS-related logs, including kernel
* /sos_commands/kubernetes/: logs related to the k8s infra and its pods
* /sos_commands/logs/: journalctl outputs

## LXC logs

The workflow also runs `sos collect` against each of the LXC containers, if they are available in the model.

The goal is to collect system level logs of the containers, as well as juju's.

These logs will be in `sos-collector-...` tarball. In that tarball, each container will have its own `sosreport-...`.

Each tarball will contain a subset of the logs mentioned in the previous section (since logs such as kern.log or k8s
do not make sense within LXC containers).

# Missing any extra logs?

If any logs are missing, e.g. logs in specific folders of /var/snap, then the steps are:
1) Extend or add a new plugin to the sosreport
2) Add it as an extra plugin (if needed) to the `integration_test_charms.yaml`.

It is important that, not only the sosreport PR has been merged upstream, but the change makes its way into the
sosreport's official snap and the [packages in Ubuntu](https://packages.ubuntu.com/search?suite=all&arch=any&searchon=names&keywords=sosreport).

# Notes

It is important to state these commands are ran at the end of the test, if it fails; therefore, if a container has been
created and destroyed during the test, it will not show in the sosreports. However, juju debug logs will contain every
log exchanged with the controller, and hence, even history of destroyed units.

If the syslog file has no recent logs, then check the /sos_commands/logs for the journalctl outputs. Normally, they will
correspond to the same logs but journalctl may be more up-to-date.

