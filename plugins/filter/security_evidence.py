"""Evidence states are distinct from Ansible task success/changed flags."""
def security_assessment(name, observed=None, expected=None, available=True, enabled=True, applied=False, failed=False):
    if not enabled: status = "not_run"
    elif failed: status = "failed"
    elif not available: status = "unknown"
    elif observed != expected: status = "needs_action"
    else: status = "applied" if applied else "compliant"
    return dict(name=name, status=status, observed=observed, expected=expected)


def security_file_assessment(name, results, policies, applied=False):
    actual, expected = [], []
    available = len(results) == len(policies) and bool(policies)
    for result, target in zip(results, policies):
        stat = result.get("stat", {})
        available = available and not result.get("failed", False)
        owner = str(stat.get("uid")) if str(target["owner"]).isdigit() else stat.get("pw_name")
        group = str(stat.get("gid")) if str(target["group"]).isdigit() else stat.get("gr_name")
        actual.append(dict(path=target["path"], exists=stat.get("exists", False), mode=stat.get("mode"), owner=owner, group=group))
        expected.append(dict(path=target["path"], exists=True, mode=str(target["mode"]).zfill(4), owner=str(target["owner"]), group=str(target["group"])))
    return security_assessment(name, actual, expected, available=available, applied=applied)


def security_sshd_observed(output):
    values = dict(line.split(None, 1) for line in output.splitlines() if len(line.split(None, 1)) == 2)
    return {key: values.get(key) for key in ("clientaliveinterval", "clientalivecountmax")}


def security_auth_assessment(current, verified, targets, applied=False):
    rows = verified if verified and all("stdout" in r for r in verified) else current
    available = len(rows) == len(targets) and all(r.get("rc", 1) == 0 for r in rows)
    observed = {row.get("item"): row.get("stdout", "").strip() for row in rows}
    return security_assessment("CephX 인증", observed, targets, available=available, applied=applied)

class FilterModule:
    def filters(self):
        return {"security_assessment": security_assessment, "security_file_assessment": security_file_assessment,
                "security_sshd_observed": security_sshd_observed, "security_auth_assessment": security_auth_assessment}
