#!/usr/bin/python
"""Create a local log snapshot once per operation id, preserving absolute paths."""
from ansible.module_utils.basic import AnsibleModule
import glob
import os
from pathlib import Path
import re
import shutil
import tempfile


def snapshot(patterns, destination, snapshot_id, check=False):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]{0,63}", snapshot_id):
        raise ValueError("invalid snapshot id")
    dest = Path(destination)
    final = dest / snapshot_id
    if (final / ".complete").is_file():
        return False
    if final.exists():
        raise ValueError("incomplete snapshot exists; inspect it before retrying")
    files = sorted({Path(p) for pattern in patterns for p in glob.glob(pattern) if Path(p).is_file() and not Path(p).is_symlink()})
    if not files:
        raise ValueError("no source log files matched")
    if check:
        return True
    dest.mkdir(mode=0o750, parents=True, exist_ok=True)
    temporary = Path(tempfile.mkdtemp(prefix=".snapshot-", dir=dest))
    try:
        for source in files:
            target = temporary / str(source.absolute()).lstrip("/")
            target.parent.mkdir(mode=0o750, parents=True, exist_ok=True)
            shutil.copy2(source, target)
        (temporary / ".complete").touch(mode=0o600)
        # rename is atomic; an existing nonempty snapshot is never overwritten.
        os.rename(temporary, final)
    finally:
        if temporary.exists(): shutil.rmtree(temporary)
    return True


def main():
    module = AnsibleModule(argument_spec=dict(patterns=dict(type="list", elements="str", required=True),
        destination=dict(type="path", required=True), snapshot_id=dict(type="str", required=True)), supports_check_mode=True)
    try:
        changed = snapshot(module.params["patterns"], module.params["destination"], module.params["snapshot_id"], module.check_mode)
    except (OSError, ValueError) as exc:
        module.fail_json(msg=str(exc))
    module.exit_json(changed=changed)

if __name__ == "__main__": main()
