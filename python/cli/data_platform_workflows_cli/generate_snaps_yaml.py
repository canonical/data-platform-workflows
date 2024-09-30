import yaml
import argparse
import pathlib
import json

from . import github_actions

UNCONSIDERED_SNAPS = ["lxd", "snapd"]

def generate_snaps_yaml(snap_table, canonical_livepatch, snaps_file_path) -> bool:
    """Update snaps.yaml file for new revisions. Returns True if a change was made."""
    snap_table_entries = snap_table.splitlines()[1:]
    
    # extract channel and revision for `canonical-livepatch` charm
    livepatch_line = canonical_livepatch.strip()
    livepatch_channel, livepatch_revision = livepatch_line.split(":")
    livepatch_revision = livepatch_revision.strip(" ()")

    packages = []
    needs_update = False

    for snap_entry in snap_table_entries:
        columns = snap_entry.split()
        if columns[0] not in UNCONSIDERED_SNAPS:
            package = {
                "name": columns[0],
                "revision": int(columns[1]),
                "push_channel": columns[2]
            }
            packages.append(package)

    packages.append({
        "name": "canonical-livepatch",
        "revision": livepatch_revision,
        "push_channel": livepatch_channel
    })
    new_data = {"packages": packages}
    
    try:
        old_yaml = pathlib.Path(snaps_file_path).read_text()
    except FileNotFoundError:
        needs_update = True
    else:
        old_data = yaml.safe_load(old_yaml)
        needs_update = new_data != old_data

    if not needs_update:
        return False

    with open(snaps_file_path, "w") as yaml_file:
        yaml.dump(new_data, yaml_file)
    return True

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('snap_table')
    parser.add_argument('canonical_livepatch')
    parser.add_argument('snaps_file_path')
    args = parser.parse_args()

    is_yaml_updated = generate_snaps_yaml(args.snap_table, args.canonical_livepatch, args.snaps_file_path)

    github_actions.output["updates_available"] = json.dumps(is_yaml_updated)
