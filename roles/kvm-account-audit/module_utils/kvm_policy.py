"""Pure account policy: unknown login history never authorizes automatic locking."""
import re


def members(passwd_text, group_text, groups):
    users = {}
    for line in passwd_text.splitlines():
        fields = line.split(":")
        if len(fields) == 7:
            users[fields[0]] = {"name": fields[0], "uid": int(fields[2]), "gid": int(fields[3])}
    selected = set()
    for line in group_text.splitlines():
        fields = line.split(":")
        if len(fields) == 4 and fields[0] in groups:
            gid = int(fields[2])
            selected.update(name for name in fields[3].split(",") if name in users)
            selected.update(name for name, user in users.items() if user["gid"] == gid)
    return [users[name] for name in sorted(selected)]


def login_date(output):
    if "Never logged in" in output:
        return "never", None
    match = re.search(r"(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)\s+\w{3}\s+\d{1,2}\s+\d{2}:\d{2}:\d{2}\s+(?:[+-]\d{4}|\S+)\s+\d{4}", output)
    return ("known", match.group(0)) if match else ("unknown", None)


def classify(accounts, inactivity_days, restriction_days, protected, retired):
    if inactivity_days < 0 or restriction_days < inactivity_days:
        raise ValueError("restriction_days must be >= inactivity_days >= 0")
    inactive, lock, delete, unknown = [], [], [], []
    for row in accounts:
        name = row["name"]
        if name in protected:
            continue
        if name in retired:
            inactive.append(row)
            lock.append(name)
            delete.append(name)
            continue
        days = row.get("days")
        if row.get("status") == "never":
            # Account creation age is unknown. Report, but never auto-lock.
            inactive.append(row)
            continue
        if row.get("status") != "known" or days is None or int(days) < 0:
            unknown.append(name)
            continue
        if int(days) >= inactivity_days:
            inactive.append(row)
        if int(days) >= restriction_days:
            lock.append(name)
    return {"inactive": inactive, "lock_targets": sorted(set(lock)),
            "delete_targets": sorted(set(delete)), "unknown": sorted(set(unknown))}
