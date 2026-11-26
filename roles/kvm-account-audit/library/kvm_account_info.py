#!/usr/bin/python
"""Read-only KVM group membership and last-login inspection."""
from ansible.module_utils.basic import AnsibleModule
from ansible.module_utils.kvm_policy import members, login_date, classify
import time


def main():
    module = AnsibleModule(argument_spec=dict(
        groups=dict(type="list", elements="str", required=True),
        protected=dict(type="list", elements="str", default=[]),
        retired=dict(type="list", elements="str", default=[]),
        uid_min=dict(type="int", default=1000),
        inactivity_days=dict(type="int", default=30),
        restriction_days=dict(type="int", default=60)), supports_check_mode=True)
    p = module.params
    passwd_rc, passwd, err = module.run_command(["getent", "passwd"])
    group_rc, groups, group_err = module.run_command(["getent", "group"])
    if passwd_rc or group_rc:
        module.fail_json(msg="Account database unavailable", details=err or group_err)
    selected = {row["name"]: row for row in members(passwd, groups, p["groups"])}
    for line in passwd.splitlines():
        fields = line.split(":")
        if fields[0] in p["retired"]:
            selected[fields[0]] = {"name": fields[0], "uid": int(fields[2])}
    accounts = []
    for name, user in sorted(selected.items()):
        if name in p["protected"] or (user["uid"] < p["uid_min"] and name not in p["retired"]):
            continue
        if name in p["retired"]:
            accounts.append(dict(name=name, status="retired", days=None))
            continue
        rc, out, _ = module.run_command(["lastlog", "-u", name], environ_update={"LC_ALL": "C"})
        status, date = login_date(out) if rc == 0 else ("unknown", None)
        days = None
        if date:
            rc, epoch, _ = module.run_command(["date", "-d", date, "+%s"], environ_update={"LC_ALL": "C"})
            if rc == 0 and epoch.strip().isdigit():
                days = (int(time.time()) - int(epoch.strip())) // 86400
            else:
                status = "unknown"
        accounts.append(dict(name=name, status=status, days=days))
    try:
        result = classify(accounts, p["inactivity_days"], p["restriction_days"], set(p["protected"]), set(p["retired"]))
    except ValueError as exc:
        module.fail_json(msg=str(exc))
    module.exit_json(changed=False, accounts=accounts, **result)


if __name__ == "__main__":
    main()
