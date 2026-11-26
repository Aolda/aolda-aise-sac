#!/usr/bin/python
"""Validate the complete sshd configuration and restore a rejected drop-in."""
from ansible.module_utils.basic import AnsibleModule
import os
from pathlib import Path
import tempfile


def atomic_write(path, content, mode=0o644, ownership=None):
    fd, temporary = tempfile.mkstemp(prefix=".aise-sshd-", dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(content)
            stream.flush()
            os.fsync(stream.fileno())
        os.chmod(temporary, mode)
        if ownership is not None: os.chown(temporary, *ownership)
        os.replace(temporary, path)
    finally:
        if os.path.exists(temporary): os.unlink(temporary)


def apply_dropin(path, content, expected, runner, check=False, binary="/usr/sbin/sshd"):
    path = Path(path)
    if path.is_symlink(): raise ValueError("refusing symlink drop-in")
    old = path.read_bytes() if path.exists() else None
    metadata = path.stat() if path.exists() else None
    changed = old != content.encode()
    if check: return changed
    rc, _, error = runner([binary, "-t"])
    if rc: raise ValueError("existing sshd configuration is invalid: " + error)
    if changed:
        if old is not None: atomic_write(Path(str(path) + ".aise-backup"), old, 0o600)
        atomic_write(path, content.encode())
    try:
        rc, _, error = runner([binary, "-t"])
        if rc: raise ValueError("new sshd configuration rejected: " + error)
        rc, output, error = runner([binary, "-T"])
        if rc: raise ValueError("cannot read effective sshd settings: " + error)
        actual = dict(line.split(None, 1) for line in output.splitlines() if len(line.split(None, 1)) == 2)
        if any(actual.get(key.lower()) != str(value) for key, value in expected.items()):
            raise ValueError("effective sshd settings differ from requested policy")
    except Exception:
        if changed:
            if old is None: path.unlink()
            else: atomic_write(path, old, metadata.st_mode & 0o7777, (metadata.st_uid, metadata.st_gid))
        raise
    return changed


def main():
    module = AnsibleModule(argument_spec=dict(path=dict(type="path", required=True),
        content=dict(type="str", required=True), expected=dict(type="dict", required=True)), supports_check_mode=True)
    try:
        changed = apply_dropin(module.params["path"], module.params["content"], module.params["expected"], module.run_command, module.check_mode)
    except (OSError, ValueError) as exc: module.fail_json(msg=str(exc))
    module.exit_json(changed=changed)

if __name__ == "__main__": main()
