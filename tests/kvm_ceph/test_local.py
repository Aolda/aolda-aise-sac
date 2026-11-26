import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]
ANSIBLE = str(Path(sys.executable).with_name("ansible-playbook"))

class RealFileIntegration(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="aise-test-")
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.key = self.base / "admin.keyring"
        self.key.write_text("synthetic-test-key-only")
        self.key.chmod(0o644)

    def run_role(self, apply=False, mode="report", check=False):
        variables = dict(ansible_become=False, ansible_python_interpreter=sys.executable, fixture_path=str(self.key), fixture_owner=str(os.getuid()),
                         fixture_group=str(os.getgid()), apply_policy=apply, security_action_mode=mode)
        env = dict(os.environ, ANSIBLE_HOME=str(self.base / "ansible"),
                   AISE_REPORT_DIR=str(self.base / "reports"), ANSIBLE_NOCOLOR="1")
        cmd = [ANSIBLE, "tests/kvm_ceph/keyring_local.yml", "-i", "localhost,", "-e", json.dumps(variables)]
        if check: cmd.append("--check")
        result = subprocess.run(cmd, cwd=ROOT, env=env, text=True, capture_output=True)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        return result.stdout

    def test_report_and_unapproved_enforce_do_not_write(self):
        for apply, mode in [(False, "report"), (True, "report"), (False, "enforce")]:
            self.run_role(apply, mode)
            self.assertEqual(self.key.stat().st_mode & 0o777, 0o644)

    def test_explicit_check_never_writes(self):
        self.run_role(True, "enforce", check=True)
        self.assertEqual(self.key.stat().st_mode & 0o777, 0o644)

    def test_apply_twice_then_repair_drift(self):
        self.run_role(True, "enforce")
        self.assertEqual(self.key.stat().st_mode & 0o777, 0o600)
        second = self.run_role(True, "enforce")
        self.assertRegex(second, r"changed=0\s")
        self.key.chmod(0o644)
        self.run_role(True, "enforce")
        self.assertEqual(self.key.stat().st_mode & 0o777, 0o600)

if __name__ == "__main__": unittest.main()
