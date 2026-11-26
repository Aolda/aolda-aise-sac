import importlib.util
from pathlib import Path
import tempfile
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("ssh_transaction", ROOT / "plugins/modules/security_sshd_dropin.py")
ssh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ssh)

class SshTransactionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "policy.conf"
        self.path.write_text("old config")
        self.path.chmod(0o640)

    def valid(self, args):
        return (0, "clientaliveinterval 300\n", "") if args[-1] == "-T" else (0, "", "")

    def test_success_and_second_apply(self):
        self.assertTrue(ssh.apply_dropin(self.path, "new config", {"clientaliveinterval": 300}, self.valid))
        self.assertFalse(ssh.apply_dropin(self.path, "new config", {"clientaliveinterval": 300}, self.valid))
        self.assertEqual(Path(str(self.path) + ".aise-backup").read_text(), "old config")

    def test_effective_value_mismatch_restores_original(self):
        with self.assertRaises(ValueError): ssh.apply_dropin(self.path, "new config", {"clientaliveinterval": 600}, self.valid)
        self.assertEqual(self.path.read_text(), "old config")
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o640)

    def test_rejected_new_file_is_removed(self):
        self.path.unlink()
        with self.assertRaises(ValueError): ssh.apply_dropin(self.path, "new config", {"clientaliveinterval": 600}, self.valid)
        self.assertFalse(self.path.exists())

    def test_invalid_existing_config_not_modified(self):
        with self.assertRaises(ValueError): ssh.apply_dropin(self.path, "new config", {}, lambda args: (1, "", "invalid"))
        self.assertEqual(self.path.read_text(), "old config")
        self.assertFalse(Path(str(self.path) + ".aise-backup").exists())

    def test_new_syntax_failure_rolls_back(self):
        calls = []
        def runner(args):
            calls.append(args)
            return (1, "", "invalid") if len(calls) == 2 else (0, "", "")
        with self.assertRaises(ValueError): ssh.apply_dropin(self.path, "new", {}, runner)
        self.assertEqual(self.path.read_text(), "old config")

    def test_check_mode_does_not_write_or_invoke_sshd(self):
        def fail(args): self.fail("check mode executed external command")
        self.assertTrue(ssh.apply_dropin(self.path, "new", {}, fail, check=True))
        self.assertEqual(self.path.read_text(), "old config")

    def test_same_content_permission_drift_is_repaired(self):
        self.path.write_text("same config")
        self.path.chmod(0o777)
        self.assertTrue(ssh.apply_dropin(self.path, "same config", {"clientaliveinterval": 300}, self.valid))
        self.assertEqual(self.path.stat().st_mode & 0o777, 0o644)
        self.assertFalse(ssh.apply_dropin(self.path, "same config", {"clientaliveinterval": 300}, self.valid))

    def test_symlink_target_rejected(self):
        link = self.path.parent / "link"
        link.symlink_to(self.path)
        with self.assertRaises(ValueError): ssh.apply_dropin(link, "new", {}, self.valid)

class OperationContracts(unittest.TestCase):
    def test_patch_modes_do_not_misrepresent_security_updates(self):
        for role in ["kvm-account-audit", "ceph-security-baseline"]:
            tasks = yaml.safe_load((ROOT / "roles" / role / "tasks/patch.yml").read_text())
            gate = next(t["ansible.builtin.assert"]["that"] for t in tasks if "패치 모드 및 유지보수 조건" in t["name"])
            self.assertIn("['report', 'latest', 'specific_version']", str(gate))
            self.assertIn("ansible_play_batch | length == 1", str(gate))
            self.assertIn("patch_precheck_commands | length > 0", str(gate))
            self.assertIn("patch_postcheck_commands | length > 0", str(gate))

    def test_reboot_requires_actual_package_change(self):
        for role in ["kvm-account-audit", "ceph-security-baseline"]:
            tasks = yaml.safe_load((ROOT / "roles" / role / "tasks/patch.yml").read_text())
            reboot = next(t for t in tasks if "ansible.builtin.reboot" in t)
            self.assertIn("changed | default(false)", str(reboot["when"]))
            self.assertIn("reboot_required.stat.exists", str(reboot["when"]))

    def test_baseline_serializes_hosts_and_stops_on_error(self):
        plays = yaml.safe_load((ROOT / "playbooks/security_baseline.yml").read_text())
        for play in plays[:2]:
            self.assertEqual(play["serial"], 1)
            self.assertTrue(play["any_errors_fatal"])

    def test_platform_gate_requires_actual_distribution_and_layout(self):
        for role in ["kvm-account-audit", "ceph-security-baseline"]:
            tasks = yaml.safe_load((ROOT / "roles" / role / "tasks/preflight.yml").read_text())
            expression = str(next(t["ansible.builtin.set_fact"] for t in tasks if "실행 환경 판정" in t["name"]))
            self.assertIn("Ubuntu", expression)
            self.assertIn("24.04", expression)
            self.assertIn("host_packages", expression)

if __name__ == "__main__": unittest.main()

log_spec = importlib.util.spec_from_file_location("log_info", ROOT / "plugins/modules/security_logrotate_info.py")
log_info = importlib.util.module_from_spec(log_spec)
log_spec.loader.exec_module(log_info)

class LogConflictTests(unittest.TestCase):
    def test_matching_paths_detected_and_own_fragment_ignored(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            own = root / "managed"
            own.write_text("/var/log/libvirt/*.log {\n}")
            self.assertEqual(log_info.conflicts(root, own, ["/var/log/libvirt/*.log"]), [])
            (root / "other").write_text("/var/log/libvirt/*.log {\n}")
            self.assertEqual(len(log_info.conflicts(root, own, ["/var/log/libvirt/*.log"])), 1)

    def test_overlapping_globs_use_existing_files(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            conf = root / "conf"
            conf.mkdir()
            log = root / "qemu.log"
            log.touch()
            (conf / "other").write_text(str(root / "*.log") + " {\n}")
            self.assertEqual(len(log_info.conflicts(conf, conf / "managed", [str(log)])), 1)

    def test_comments_are_ignored(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            (root / "other").write_text("# /var/log/libvirt/*.log\n")
            self.assertEqual(log_info.conflicts(root, root / "managed", ["/var/log/libvirt/*.log"]), [])
