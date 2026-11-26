import importlib.util
from pathlib import Path
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[2]
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT / path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result

evidence = load("evidence", "plugins/filter/security_evidence.py")
report = load("report", "plugins/callback/security_report.py")

class EvidenceTests(unittest.TestCase):
    def test_successful_query_is_not_automatically_compliant(self):
        self.assertEqual(evidence.security_assessment("policy", "none", "cephx")["status"], "needs_action")

    def test_unavailable_values_cannot_be_compliant(self):
        self.assertEqual(evidence.security_assessment("policy", available=False)["status"], "unknown")

    def test_disabled_and_failed_are_separate_states(self):
        self.assertEqual(evidence.security_assessment("p", enabled=False)["status"], "not_run")
        self.assertEqual(evidence.security_assessment("p", failed=True)["status"], "failed")

    def test_applied_requires_verified_target(self):
        self.assertEqual(evidence.security_assessment("p", 1, 2, applied=True)["status"], "needs_action")
        self.assertEqual(evidence.security_assessment("p", 2, 2, applied=True)["status"], "applied")
        self.assertEqual(evidence.security_assessment("p", 2, 2)["status"], "compliant")

    def test_missing_file_is_a_finding(self):
        targets = [dict(path="/x", owner="root", group="root", mode="0600")]
        result = evidence.security_file_assessment("key", [dict(stat=dict(exists=False))], targets)
        self.assertEqual(result["status"], "needs_action")

    def test_numeric_owners_and_mode_are_normalized(self):
        targets = [dict(path="/x", owner="501", group="20", mode="600")]
        stats = [dict(stat=dict(exists=True, uid=501, gid=20, mode="0600"))]
        self.assertEqual(evidence.security_file_assessment("key", stats, targets)["status"], "compliant")

    def test_partial_or_failed_file_queries_are_unknown(self):
        targets = [dict(path="/x", owner="root", group="root", mode="0600")]
        self.assertEqual(evidence.security_file_assessment("key", [], targets)["status"], "unknown")
        self.assertEqual(evidence.security_file_assessment("key", [dict(failed=True)], targets)["status"], "unknown")

    def test_auth_uses_final_verified_values(self):
        current = [dict(item="auth", stdout="none", rc=0)]
        verified = [dict(item="auth", stdout="cephx", rc=0)]
        self.assertEqual(evidence.security_auth_assessment(current, verified, {"auth":"cephx"}, True)["status"], "applied")
        self.assertEqual(evidence.security_auth_assessment(current, [], {"auth":"cephx"})["status"], "needs_action")

    def test_auth_query_failure_is_unknown(self):
        self.assertEqual(evidence.security_auth_assessment([dict(item="auth", stdout="", rc=9)], [], {"auth":"cephx"})["status"], "unknown")

    def test_sshd_only_compares_requested_fields(self):
        self.assertEqual(evidence.security_sshd_observed("port 22\nclientaliveinterval 300\nclientalivecountmax 2\n"), dict(clientaliveinterval="300", clientalivecountmax="2"))

class CallbackCompatibilityTests(unittest.TestCase):
    def setUp(self):
        self.callback = report.CallbackModule()
        self.callback.finished_at = self.callback.started_at
        self.row = dict(task="read-only query", host="test", changed=False, failed=False, skipped=False)

    def test_scoped_report_never_counts_query_success_as_compliance(self):
        output = self.callback._render("ceph-security-baseline", [self.row], "report.md")
        self.assertIn("수집된 정책 근거가 없습니다", output)
        self.assertIn("기준 충족 판정 아님", output)
        self.assertIn("|기준 충족|0|", output)

    def test_other_roles_keep_legacy_report(self):
        output = self.callback._render("report-test-baseline", [self.row], "report.md")
        self.assertIn("|총 검사 정책 수|조치 완료 정책 수|조치 필요 정책 수|", output)
        self.assertIn("|1|1|0|", output)

    def test_observed_evidence_is_escaped(self):
        self.callback.policy_evidence[("kvm-account-audit", "test", "policy")] = dict(name="x|y", status="unknown", observed="a\nb", expected=None)
        output = self.callback._render("kvm-account-audit", [], "report.md")
        self.assertIn("x\\|y", output)
        self.assertIn("a<br>b", output)
        self.assertIn("|점검 불가|1|", output)

if __name__ == "__main__": unittest.main()
