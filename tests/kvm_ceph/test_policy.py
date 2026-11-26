import importlib.util
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("kvm_policy", ROOT / "roles/kvm-account-audit/module_utils/kvm_policy.py")
policy = importlib.util.module_from_spec(spec)
spec.loader.exec_module(policy)

class AccountPolicyTests(unittest.TestCase):
    def row(self, days, name="alice", status="known"):
        return dict(name=name, days=days, status=status)

    def classify(self, rows, protected=(), retired=()):
        return policy.classify(rows, 30, 60, set(protected), set(retired))

    def test_boundary_29_30_59_60_61(self):
        for days in [29, 30, 59, 60, 61]:
            with self.subTest(days=days):
                result = self.classify([self.row(days)])
                self.assertEqual(bool(result["inactive"]), days >= 30)
                self.assertEqual(bool(result["lock_targets"]), days >= 60)

    def test_three_digit_days_are_numeric(self):
        for days in [100, 365, "100"]:
            self.assertEqual(self.classify([self.row(days)])["lock_targets"], ["alice"])

    def test_unknown_and_future_dates_never_lock(self):
        for row in [self.row(None, status="unknown"), self.row(-1)]:
            result = self.classify([row])
            self.assertEqual(result["lock_targets"], [])
            self.assertEqual(result["unknown"], ["alice"])

    def test_never_logged_in_requires_manual_review(self):
        result = self.classify([self.row(None, status="never")])
        self.assertEqual(len(result["inactive"]), 1)
        self.assertEqual(result["lock_targets"], [])

    def test_retired_account_is_explicit_target(self):
        result = self.classify([self.row(None, status="retired")], retired=["alice"])
        self.assertEqual(result["delete_targets"], ["alice"])
        self.assertEqual(result["lock_targets"], ["alice"])

    def test_protected_overrides_retired(self):
        result = self.classify([self.row(365)], protected=["alice"], retired=["alice"])
        self.assertEqual(result["delete_targets"], [])
        self.assertEqual(result["lock_targets"], [])

    def test_primary_and_secondary_members_deduplicate(self):
        passwd = "alice:x:1000:100:/home/a:/bin/bash\nbob:x:1001:200:/home/b:/bin/bash"
        # getent passwd records must have seven fields.
        passwd = "alice:x:1000:100::/home/a:/bin/bash\nbob:x:1001:200::/home/b:/bin/bash"
        groups = "kvm:x:100:alice,bob,missing\nqemu:x:200:bob"
        self.assertEqual([r["name"] for r in policy.members(passwd, groups, ["kvm", "qemu"])], ["alice", "bob"])

    def test_missing_group_returns_empty(self):
        self.assertEqual(policy.members("", "", ["kvm"]), [])

    def test_login_parser_accepts_c_locale(self):
        status, date = policy.login_date("alice pts/0 10.0.0.1 Thu Nov 26 10:10:10 +0900 2026")
        self.assertEqual(status, "known")
        self.assertTrue(date.endswith("2026"))

    def test_login_parser_unknown_is_not_never(self):
        self.assertEqual(policy.login_date("command failed"), ("unknown", None))
        self.assertEqual(policy.login_date("**Never logged in**"), ("never", None))

    def test_invalid_thresholds_rejected(self):
        for low, high in [(-1, 60), (60, 30)]:
            with self.assertRaises(ValueError): policy.classify([], low, high, set(), set())

class SafetyContracts(unittest.TestCase):
    def tasks(self):
        for role in ("kvm-account-audit", "ceph-security-baseline"):
            for path in (ROOT / "roles" / role / "tasks").glob("*.yml"):
                for task in yaml.safe_load(path.read_text()): yield path, task

    def test_every_mutation_requires_apply_policy(self):
        mutations = {"file", "template", "copy", "apt", "user", "group", "reboot", "command", "shell"}
        for path, task in self.tasks():
            action = next((k for k in task if k.startswith("ansible.builtin.")), "")
            if action.split(".")[-1] not in mutations or task.get("changed_when") is False:
                continue
            with self.subTest(path=path.name, task=task["name"]):
                self.assertIn("apply_policy", str(task.get("when")))
                self.assertIn("security_action_mode", str(task.get("when")))

    def test_read_only_commands_execute_in_check_mode(self):
        for path, task in self.tasks():
            if any(k in task for k in ("ansible.builtin.command", "ansible.builtin.shell")) and task.get("changed_when") is False:
                self.assertIs(task.get("check_mode"), False, str(path))

    def test_keyring_content_hidden_from_logs_and_diff(self):
        tasks = yaml.safe_load((ROOT / "roles/ceph-security-baseline/tasks/auth.yml").read_text())
        deploy = next(t for t in tasks if "keyring_content" in str(t))
        self.assertIs(deploy["no_log"], True)
        self.assertIs(deploy["diff"], False)
        self.assertIn("not ceph_auth_report_only | bool", deploy["when"])

    def test_no_implicit_full_sudo(self):
        defaults = yaml.safe_load((ROOT / "roles/ceph-security-baseline/defaults/main.yml").read_text())
        self.assertEqual(defaults["ceph_admin_sudo_commands"], [])
        self.assertEqual(defaults["ceph_admin_groups"], [])
        self.assertFalse(defaults["ceph_admin_sudo_nopasswd"])

if __name__ == "__main__": unittest.main()

key_spec = importlib.util.spec_from_file_location("ceph_keys", ROOT / "roles/ceph-security-baseline/filter_plugins/ceph_keys.py")
keys = importlib.util.module_from_spec(key_spec)
key_spec.loader.exec_module(keys)

class AuthorizedKeyTests(unittest.TestCase):
    def test_append_preserves_existing_and_is_stable(self):
        first = keys.ceph_key_content("ssh-ed25519 old\n", ["ssh-ed25519 new"])
        self.assertIn("ssh-ed25519 old", first)
        self.assertEqual(keys.ceph_key_content(first, ["ssh-ed25519 new"]), first)

    def test_replacement_requires_confirmation(self):
        with self.assertRaises(ValueError): keys.ceph_key_content("old", ["new"], True)
        self.assertEqual(keys.ceph_key_content("old", ["new"], True, True), "new\n")

    def test_empty_or_multiline_keys_rejected(self):
        for desired in [[], [""], ["a\nb"], "key"]:
            with self.assertRaises(ValueError): keys.ceph_key_content("old", desired)

    def test_management_key_must_survive_replacement(self):
        with self.assertRaises(ValueError): keys.ceph_key_content("old", ["new"], True, True, ["old"])
