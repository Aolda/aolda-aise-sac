import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("snapshot", ROOT / "roles/kvm-account-audit/library/kvm_log_snapshot.py")
snapshot = importlib.util.module_from_spec(spec)
spec.loader.exec_module(snapshot)

class SnapshotTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.log = self.root / "source.log"
        self.log.write_text("first")
        self.dest = self.root / "backup"

    def test_same_operation_does_not_copy_again(self):
        self.assertTrue(snapshot.snapshot([str(self.log)], str(self.dest), "run-1"))
        self.log.write_text("second")
        self.assertFalse(snapshot.snapshot([str(self.log)], str(self.dest), "run-1"))
        copied = self.dest / "run-1" / str(self.log).lstrip("/")
        self.assertEqual(copied.read_text(), "first")

    def test_same_basename_keeps_both_sources(self):
        other = self.root / "other" / "source.log"
        other.parent.mkdir()
        other.write_text("other")
        snapshot.snapshot([str(self.log), str(other)], str(self.dest), "run-1")
        self.assertEqual(len(list(self.dest.rglob("source.log"))), 2)

    def test_check_mode_creates_nothing(self):
        self.assertTrue(snapshot.snapshot([str(self.log)], str(self.dest), "run-1", True))
        self.assertFalse(self.dest.exists())

    def test_invalid_id_rejected(self):
        for value in ["", "../escape", "/absolute", "x/y"]:
            with self.assertRaises(ValueError): snapshot.snapshot([str(self.log)], str(self.dest), value)

    def test_incomplete_snapshot_is_not_overwritten(self):
        (self.dest / "run-1").mkdir(parents=True)
        with self.assertRaises(ValueError): snapshot.snapshot([str(self.log)], str(self.dest), "run-1")

    def test_empty_match_is_not_success(self):
        with self.assertRaises(ValueError): snapshot.snapshot([str(self.root / "missing")], str(self.dest), "run-1")

    def test_symlink_source_is_not_followed(self):
        link = self.root / "link"
        link.symlink_to(self.log)
        with self.assertRaises(ValueError): snapshot.snapshot([str(link)], str(self.dest), "run-1")

class CephCommandIntegration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="aise-ceph-test-")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.state = self.root / "state.json"
        self.state.write_text(json.dumps(dict(auth_cluster_required="none", auth_service_required="none", auth_client_required="none")))
        self.calls = self.root / "writes"
        fake = self.root / "ceph"
        fake.write_text("#!" + sys.executable + "\n" + """import json, os, pathlib, sys
p = pathlib.Path(os.environ['AISE_FAKE_STATE'])
a = sys.argv[1:]
if os.environ.get('AISE_FAKE_FAIL') == '1': sys.exit(9)
s = json.loads(p.read_text())
if a[:2] == ['config','get']: print(s[a[3]])
elif a[:2] == ['config','set']:
 s[a[3]]=a[4]; p.write_text(json.dumps(s))
 with open(os.environ['AISE_FAKE_WRITES'],'a') as log: print(a[3], file=log)
else: sys.exit(8)
""")
        fake.chmod(0o755)

    def run_auth(self, check=False, fail=False, apply=True):
        variables = dict(ansible_become=False, ansible_python_interpreter=sys.executable,
            apply_policy=apply, security_action_mode="enforce", enable_cephx_enforcement=True,
            ceph_auth_report_only=False, ceph_deploy_keyrings=False, fake_bin=str(self.root),
            fake_state=str(self.state), fake_writes=str(self.calls), fake_fail="1" if fail else "0")
        env = dict(os.environ, ANSIBLE_HOME=str(self.root / "ansible"), AISE_REPORT_DIR=str(self.root / "reports"), ANSIBLE_NOCOLOR="1")
        cmd = [str(Path(sys.executable).with_name("ansible-playbook")), "tests/kvm_ceph/auth_local.yml", "-i", "localhost,", "-e", json.dumps(variables)]
        if check: cmd.append("--check")
        return subprocess.run(cmd, cwd=ROOT, env=env, capture_output=True, text=True)

    def test_only_different_values_are_written_once(self):
        for _ in range(2):
            result = self.run_auth()
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertEqual(len(self.calls.read_text().splitlines()), 3)
        self.assertRegex(result.stdout, r"changed=0\s")
        self.assertEqual(set(json.loads(self.state.read_text()).values()), {"cephx"})

    def test_query_failure_prevents_writes(self):
        result = self.run_auth(fail=True)
        self.assertNotEqual(result.returncode, 0)
        self.assertFalse(self.calls.exists())

    def test_check_and_report_never_write(self):
        for check, apply in [(True, True), (False, False)]:
            result = self.run_auth(check=check, apply=apply)
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            self.assertFalse(self.calls.exists())

class RepeatedActionContracts(unittest.TestCase):
    def test_no_unconditional_selinux_reboot(self):
        tasks = yaml.safe_load((ROOT / "roles/ceph-security-baseline/tasks/selinux.yml").read_text())
        self.assertFalse(any("ansible.builtin.reboot" in t for t in tasks))
        setter = next(t for t in tasks if t["name"] == "Ceph SELinux 상태 설정")
        self.assertIn("ceph_selinux_current.stdout | trim | lower != ceph_selinux_state", setter["when"])

    def test_manual_script_has_stable_name(self):
        tasks = yaml.safe_load((ROOT / "roles/kvm-account-audit/tasks/accounts.yml").read_text())
        task = next(t for t in tasks if "ansible.builtin.template" in t)
        self.assertNotIn("ansible_date_time", task["ansible.builtin.template"]["dest"])

    def test_ufw_uses_stateful_module(self):
        tasks = yaml.safe_load((ROOT / "roles/kvm-account-audit/tasks/ip_restrict.yml").read_text())
        self.assertEqual(sum("community.general.ufw" in t for t in tasks), 3)

if __name__ == "__main__": unittest.main()
