#!/usr/bin/python
"""Read-only detection of duplicate absolute log paths/globs in logrotate fragments."""
from ansible.module_utils.basic import AnsibleModule
import glob
from pathlib import Path
import shlex


def conflicts(directory, own_config, patterns):
    target_files = {p for pattern in patterns for p in glob.glob(pattern)}
    found = []
    for path in sorted(Path(directory).glob("*")):
        if not path.is_file() or path == Path(own_config): continue
        for line in path.read_text().splitlines():
            for token in shlex.split(line, comments=True):
                if token.startswith("/") and (token in patterns or target_files.intersection(glob.glob(token))):
                    found.append({"config": str(path), "pattern": token})
    return found


def main():
    module = AnsibleModule(argument_spec=dict(directory=dict(type="path", default="/etc/logrotate.d"),
        own_config=dict(type="path", required=True), patterns=dict(type="list", elements="str", required=True)), supports_check_mode=True)
    try: result = conflicts(**module.params)
    except (OSError, ValueError) as exc: module.fail_json(msg=str(exc))
    module.exit_json(changed=False, conflicts=result)

if __name__ == "__main__": main()
