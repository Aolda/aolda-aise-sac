from pathlib import Path
import sys
import unittest


PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from plugins.callback.security_report import CallbackModule, POLICY_CATALOGS  # noqa: E402


class SecurityReportPolicyTest(unittest.TestCase):
    def setUp(self):
        self.callback = CallbackModule()

    def test_requested_component_policy_counts(self):
        expected = {
            "db-security": 9,
            "docker-security": 20,
            "k8s-security": 5,
            "keystone-security": 4,
            "nova-security": 3,
            "cinder-security": 5,
            "glance-security": 2,
            "neutron-security": 2,
        }
        self.assertEqual(
            {role: len(POLICY_CATALOGS[role]) for role in expected}, expected
        )
        self.assertEqual(sum(expected.values()), 50)

    def test_db_task_mapping(self):
        cases = {
            ("1-1. 익명 사용자 제거", "1_accounts_password.yml"): ["DB-01"],
            ("2-3. 패스워드 정책 설정", "1_accounts_password.yml"): ["DB-02"],
            ("3-1. GRANT OPTION 회수", "2_privileges.yml"): ["DB-03"],
            ("4-1. mysql.user 권한 회수", "2_privileges.yml"): ["DB-04"],
            ("1-1. DB 구동 계정 설정", "3_root_and_logging.yml"): ["DB-05"],
            ("2-1. 설정 파일 권한", "3_root_and_logging.yml"): ["DB-06"],
            ("8-1. 인증 플러그인", "4_authentication_and_patch.yml"): ["DB-07"],
            ("3-2. Slow Query Log", "3_root_and_logging.yml"): ["DB-08"],
            ("9-1. DB 패키지 상태", "4_authentication_and_patch.yml"): ["DB-09"],
        }
        for (name, filename), expected in cases.items():
            with self.subTest(name=name):
                self.assertEqual(
                    self.callback._policy_ids("db-security", name, filename), expected
                )

    def test_kubernetes_task_file_mapping(self):
        expected = {
            "1_control_plane.yml": "K8S-01",
            "2_api_server.yml": "K8S-02",
            "3_etcd.yml": "K8S-03",
            "4_kubelet.yml": "K8S-04",
            "5_policies.yml": "K8S-05",
            "6_pod_security_checks.yml": "K8S-05",
        }
        for filename, policy_id in expected.items():
            with self.subTest(filename=filename):
                self.assertEqual(
                    self.callback._policy_ids(
                        "k8s-security", "1-1. 정책 점검", filename
                    ),
                    [policy_id],
                )

    def test_policy_statistics_are_policy_based_and_reconcile(self):
        rows = [
            self._row("DOCKER-01", evaluated=True),
            self._row("DOCKER-02", evaluated=True, changed=True),
            self._row("DOCKER-03", evaluated=True, warning=True),
            self._row("DOCKER-04", evaluated=False),
        ]
        total, completed, needed, successful, failed = self.callback._statistics(rows)
        self.assertEqual((total, completed, needed, successful, failed), (4, 1, 3, 1, 0))
        self.assertEqual(total, completed + needed)

    @staticmethod
    def _row(policy_id, evaluated, changed=False, warning=False, failed=False):
        return {
            "role": "docker-security",
            "policy_id": policy_id,
            "task": policy_id,
            "host": "localhost",
            "changed": changed,
            "failed": failed,
            "skipped": not evaluated,
            "warning": warning,
            "evaluated": evaluated,
        }


if __name__ == "__main__":
    unittest.main()
