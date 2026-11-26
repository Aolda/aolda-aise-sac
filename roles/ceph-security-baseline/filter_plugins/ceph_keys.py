"""Deterministic authorized_keys policy with explicit replacement."""
def ceph_key_content(existing, desired, replace=False, confirmed=False, required=()):
    if not isinstance(desired, list) or not desired or any(not isinstance(k, str) or not k.strip() or "\n" in k or "\r" in k for k in desired):
        raise ValueError("desired keys must be nonempty single-line strings")
    if replace and not confirmed:
        raise ValueError("replacement requires confirmation")
    lines = [] if replace else existing.splitlines()
    lines = list(dict.fromkeys(lines + desired))
    if any(key not in lines for key in required):
        raise ValueError("required management key would be removed")
    return "\n".join(lines) + "\n"

class FilterModule:
    def filters(self):
        return {"ceph_key_content": ceph_key_content}
