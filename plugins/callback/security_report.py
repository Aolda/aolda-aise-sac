"""Create one Markdown security report for each role in an ansible-playbook run."""

from __future__ import annotations

import getpass
import os
import re
from collections import OrderedDict
from datetime import datetime
from pathlib import Path

from ansible import context
from ansible.plugins.callback import CallbackBase


DOCUMENTATION = r"""
name: security_report
type: aggregate
short_description: Write security task results to a Markdown report
version_added: "1.0"
requirements:
  - Python 3
options:
  report_dir:
    description: Directory in which reports are created.
    default: reports
    env:
      - name: AISE_REPORT_DIR
    ini:
      - section: callback_security_report
        key: report_dir
  report_title:
    description: Markdown report title.
    default: 보안조치 결과 보고서
    env:
      - name: AISE_REPORT_TITLE
    ini:
      - section: callback_security_report
        key: report_title
"""

CALLBACK_VERSION = 2.0
CALLBACK_TYPE = "aggregate"
CALLBACK_NAME = "security_report"
CALLBACK_NEEDS_ENABLED = True


IGNORED_ACTIONS = {
    "ansible.builtin.gather_facts",
    "ansible.builtin.include_tasks",
    "ansible.builtin.import_tasks",
    "ansible.builtin.include_role",
    "ansible.builtin.import_role",
    "ansible.builtin.meta",
    "gather_facts",
    "include_tasks",
    "import_tasks",
    "include_role",
    "import_role",
    "meta",
}


POLICY_CATALOGS = {
    "db-security": OrderedDict(
        [
            ("DB-01", "불필요 DB 계정 제거"),
            ("DB-02", "취약한 패스워드 사용 제한"),
            ("DB-03", "타 사용자에 권한 부여 옵션 제한"),
            ("DB-04", "DB 사용자 계정 정보 테이블 접근 권한 제한"),
            ("DB-05", "root 권한으로 서버 구동 제한"),
            ("DB-06", "환경설정 파일 접근 권한 제한"),
            ("DB-07", "안전한 패스워드 암호화 알고리즘 사용"),
            ("DB-08", "로그 활성화"),
            ("DB-09", "최신 보안 패치 적용"),
        ]
    ),
    "docker-security": OrderedDict(
        [
            ("DOCKER-01", "도커 최신 보안 패치 적용"),
            ("DOCKER-02", "도커 그룹에 불필요한 사용자 제거"),
            ("DOCKER-03", "Host의 user namespaces 공유 제한"),
            ("DOCKER-04", "Docker daemon audit 설정"),
            ("DOCKER-05", "추가 권한 획득으로부터 컨테이너 제한"),
            ("DOCKER-06", "docker.service 소유권 설정"),
            ("DOCKER-07", "docker.service 파일 접근 권한 설정"),
            ("DOCKER-08", "docker.socket 소유권 설정"),
            ("DOCKER-09", "docker.socket 파일 접근 권한 설정"),
            ("DOCKER-10", "/etc/docker 소유권 설정"),
            ("DOCKER-11", "/etc/docker 파일 접근 권한 설정"),
            ("DOCKER-12", "/var/run/docker.sock 소유권 설정"),
            ("DOCKER-13", "/var/run/docker.sock 파일 접근 권한 설정"),
            ("DOCKER-14", "daemon.json 소유권 설정"),
            ("DOCKER-15", "daemon.json 파일 접근 권한 설정"),
            ("DOCKER-16", "도커를 위한 콘텐츠 신뢰성 활성화"),
            ("DOCKER-17", "컨테이너 SELinux 보안 옵션 설정"),
            ("DOCKER-18", "컨테이너에서 SSH 사용 금지"),
            ("DOCKER-19", "컨테이너에 privileged 포트 매핑 금지"),
            ("DOCKER-20", "PIDs cgroup 제한"),
        ]
    ),
    "k8s-security": OrderedDict(
        [
            ("K8S-01", "Control Plane 파일 및 PKI 권한 보호"),
            ("K8S-02", "API 서버 인증·인가 및 감사 로깅 설정"),
            ("K8S-03", "etcd 저장 데이터 암호화 및 TLS 보호"),
            ("K8S-04", "kubelet 인증·인가 및 TLS 설정"),
            ("K8S-05", "RBAC·Pod 보안·NetworkPolicy·시크릿 관리"),
        ]
    ),
    "keystone-security": OrderedDict(
        [
            ("OSAUTH-01", "Keystone TLS 설정"),
            ("OSAUTH-02", "Keystone PKI token hash 알고리즘 강화"),
            ("OSAUTH-03", "Keystone max_request_body_size 설정"),
            ("OSAUTH-04", "Keystone admin_token 비활성화"),
        ]
    ),
    "nova-security": OrderedDict(
        [
            ("OSAUTH-05", "Compute 인증을 위한 보안 프로토콜 사용"),
            ("OSAUTH-06", "Nova와 Glance의 안전한 통신"),
            ("OSAUTH-07", "Compute의 인증을 위한 Keystone 사용"),
        ]
    ),
    "cinder-security": OrderedDict(
        [
            ("OSAUTH-08", "블록스토리지 서비스 인증을 위한 TLS 활성화"),
            ("OSAUTH-09", "Cinder와 Nova의 TLS 통신"),
            ("OSAUTH-10", "Cinder와 Glance의 TLS 통신"),
            ("OSAUTH-11", "블록 스토리지 서비스의 인증을 위한 Keystone 사용"),
            ("OSAUTH-12", "블록 스토리지 서비스 요청 본문 최대 크기 설정"),
        ]
    ),
    "glance-security": OrderedDict(
        [
            ("OSAUTH-13", "이미지스토리지 서비스 인증을 위한 TLS 활성화"),
            ("OSAUTH-14", "이미지 스토리지 서비스 인증을 위한 Keystone 설정"),
        ]
    ),
    "neutron-security": OrderedDict(
        [
            ("OSAUTH-15", "네트워킹 서비스 인증을 위한 안전한 프로토콜 사용"),
            ("OSAUTH-16", "Neutron API 서버 TLS 설정"),
        ]
    ),
}

POLICY_ID_PATTERN = re.compile(r"\b(?:DB|DOCKER|K8S|OSAUTH)-\d{2}\b")
WARNING_TASK_MARKERS = (
    "경고 출력",
    "누락 경고",
    "적용 제외 안내",
    "점검 모드 안내",
    "기본 점검 모드 안내",
    "manual-required 안내",
    "확인 실패 안내",
)
COMPLIANT_WHEN_SKIPPED = {"OSAUTH-07", "OSAUTH-11"}


def _as_bool(value):
    if isinstance(value, bool):
        return value
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


def _escape_cell(value):
    return str(value).replace("|", r"\|").replace("\r", " ").replace("\n", "<br>")


def _section_label(index):
    labels = "가나다라마바사아자차카타파하"
    if index < len(labels):
        return labels[index]
    quotient, remainder = divmod(index, len(labels))
    return labels[quotient - 1] + labels[remainder]


class CallbackModule(CallbackBase):
    """Collect runner events and render the final Markdown report."""

    def __init__(self):
        super().__init__()
        self.started_at = datetime.now().astimezone()
        self.finished_at = None
        self.apply_policy = False
        self.report_title = "보안조치 결과 보고서"
        self.report_dir = "reports"
        self.playbook_name = ""
        self.inventory_sources = []
        self.target_patterns = []
        self.hosts_seen = []
        self.os_by_host = OrderedDict()
        self.roles_seen = []
        self.results = OrderedDict()
        self.policy_results = OrderedDict()

    def set_options(self, task_keys=None, var_options=None, direct=None):
        super().set_options(task_keys=task_keys, var_options=var_options, direct=direct)
        self.report_dir = self.get_option("report_dir")
        self.report_title = self.get_option("report_title")

    def v2_playbook_on_start(self, playbook):
        self.playbook_name = os.path.basename(playbook._file_name)
        inventory = getattr(playbook, "_inventory", None)
        self.inventory_sources = list(getattr(inventory, "_sources", []) or [])
        if not self.inventory_sources:
            cli_inventory = context.CLIARGS.get("inventory", ())
            if isinstance(cli_inventory, str):
                cli_inventory = [cli_inventory]
            self.inventory_sources = list(cli_inventory or [])

    def v2_playbook_on_play_start(self, play):
        pattern = str(getattr(play, "hosts", "")).strip()
        if pattern and pattern not in self.target_patterns:
            self.target_patterns.append(pattern)

        variable_manager = getattr(play, "_variable_manager", None)
        if variable_manager is None:
            return
        try:
            variables = variable_manager.get_vars(play=play)
        except Exception:
            return

        requested_apply = _as_bool(variables.get("apply_policy", False))
        cli_check = _as_bool(context.CLIARGS.get("check", False))
        self.apply_policy = requested_apply and not cli_check
        self.report_title = str(variables.get("report_title", self.report_title))
        self.report_dir = str(variables.get("report_dir", self.report_dir))

    def v2_runner_on_ok(self, result):
        self._record(result, "ok")

    def v2_runner_on_failed(self, result, ignore_errors=False):
        self._record(result, "failed")

    def v2_runner_on_unreachable(self, result):
        self._record(result, "unreachable")

    def v2_runner_on_skipped(self, result):
        self._record(result, "skipped")

    def v2_runner_item_on_ok(self, result):
        self._record(result, "ok")

    def v2_runner_item_on_failed(self, result):
        self._record(result, "failed")

    def v2_runner_item_on_skipped(self, result):
        self._record(result, "skipped")

    def _record(self, result, status):
        task = result._task
        action = getattr(task, "action", "")
        raw = result._result or {}
        host = result._host.get_name()
        if host not in self.hosts_seen:
            self.hosts_seen.append(host)
        self._collect_os_info(host, raw.get("ansible_facts", {}))

        if action in IGNORED_ACTIONS:
            return

        role = self._role_name(task)
        if role not in self.roles_seen:
            self.roles_seen.append(role)

        task_name = task.get_name().strip()
        self._record_policy_result(role, task_name, task.get_path() or "", host, raw, status)
        item = raw.get("_ansible_item_label", raw.get("item"))
        if item is not None and not isinstance(item, (dict, list)):
            task_name = f"{task_name} [{item}]"

        key = (role, task_name, host)
        changed = bool(raw.get("changed", False))
        failed = status in {"failed", "unreachable"} or bool(raw.get("failed", False))
        skipped = status == "skipped" or bool(raw.get("skipped", False))

        current = self.results.get(
            key,
            {
                "role": role,
                "task": task_name,
                "host": host,
                "changed": False,
                "failed": False,
                "skipped": True,
            },
        )
        current["changed"] = current["changed"] or changed
        current["failed"] = current["failed"] or failed
        current["skipped"] = current["skipped"] and skipped
        self.results[key] = current

    def _record_policy_result(self, role, task_name, task_path, host, raw, status):
        if role not in POLICY_CATALOGS:
            return

        policy_ids = self._policy_ids(role, task_name, task_path)
        if not policy_ids:
            return

        changed = bool(raw.get("changed", False))
        failed = status in {"failed", "unreachable"} or bool(raw.get("failed", False))
        skipped = status == "skipped" or bool(raw.get("skipped", False))
        warning_task = any(marker in task_name for marker in WARNING_TASK_MARKERS)
        warning = not skipped and warning_task

        for policy_id in policy_ids:
            if policy_id not in POLICY_CATALOGS[role]:
                continue
            key = (role, policy_id, host)
            current = self.policy_results.get(
                key,
                {
                    "role": role,
                    "policy_id": policy_id,
                    "task": f"{policy_id}. {POLICY_CATALOGS[role][policy_id]}",
                    "host": host,
                    "changed": False,
                    "failed": False,
                    "skipped": True,
                    "warning": False,
                    "evaluated": False,
                },
            )
            current["changed"] = current["changed"] or changed
            current["failed"] = current["failed"] or failed
            current["skipped"] = current["skipped"] and skipped
            current["warning"] = current["warning"] or warning
            # A skipped warning task means its violation condition evaluated false.
            # If the whole task file was excluded, no event is emitted and the
            # catalog entry remains unevaluated.
            current["evaluated"] = (
                current["evaluated"]
                or not skipped
                or warning_task
                or policy_id in COMPLIANT_WHEN_SKIPPED
            )
            self.policy_results[key] = current

    @staticmethod
    def _policy_ids(role, task_name, task_path):
        explicit_ids = POLICY_ID_PATTERN.findall(task_name)
        if explicit_ids:
            return explicit_ids

        filename = Path(task_path).name
        prefix_match = re.search(r"(?:^|: )([0-9]+)-([0-9]+)", task_name)
        major = int(prefix_match.group(1)) if prefix_match else None
        minor = int(prefix_match.group(2)) if prefix_match else None

        if role == "db-security":
            if filename == "1_accounts_password.yml":
                if "1-0-8-2." in task_name:
                    return ["DB-03", "DB-04"]
                if major == 1:
                    return ["DB-01"]
                if major == 2:
                    return ["DB-02"]
            if filename == "2_privileges.yml":
                return {3: ["DB-03"], 4: ["DB-04"]}.get(major, [])
            if filename == "3_root_and_logging.yml":
                return {1: ["DB-05"], 2: ["DB-06"], 3: ["DB-08"]}.get(major, [])
            if filename == "4_authentication_and_patch.yml":
                if major == 8:
                    return ["DB-07"]
                if major == 9 and minor in {1, 2}:
                    return ["DB-09"]
            if filename == "validate.yml" and major == 10:
                if minor in {1, 2}:
                    return ["DB-06"]
                if minor in {3, 4, 5}:
                    return ["DB-05"]
                if minor in {6, 7, 8}:
                    return ["DB-08"]
                if minor in {9, 10, 11}:
                    return ["DB-02"]

        if role == "k8s-security":
            file_policy = {
                "1_control_plane.yml": "K8S-01",
                "2_api_server.yml": "K8S-02",
                "3_etcd.yml": "K8S-03",
                "4_kubelet.yml": "K8S-04",
                "5_policies.yml": "K8S-05",
                "6_pod_security_checks.yml": "K8S-05",
            }.get(filename)
            if file_policy:
                return [file_policy]
            if filename == "validate.yml" and major == 7:
                if minor in {4, 5}:
                    return ["K8S-02"]
                if minor in {6, 7}:
                    return ["K8S-03"]
                if minor in {8, 9, 10}:
                    return ["K8S-04"]
        return []

    def _collect_os_info(self, host, facts):
        if not facts:
            return
        distribution = facts.get("ansible_distribution", facts.get("distribution"))
        version = facts.get(
            "ansible_distribution_version", facts.get("distribution_version")
        )
        if distribution:
            self.os_by_host[host] = " ".join(
                part for part in (str(distribution), str(version or "")) if part
            )

    @staticmethod
    def _role_name(task):
        role = getattr(task, "_role", None)
        if role is not None:
            name = role.get_name()
            if name:
                return name.split(":")[-1]

        path = task.get_path() or ""
        match = re.search(r"(?:^|/)roles/([^/]+)/", path)
        return match.group(1) if match else "playbook"

    def v2_playbook_on_stats(self, stats):
        self.finished_at = datetime.now().astimezone()
        grouped = self._results_by_role()
        for role, rows in grouped.items():
            report_path = self._report_path(role)
            try:
                report_path.parent.mkdir(parents=True, exist_ok=True)
                report_path.write_text(
                    self._render(role, rows, report_path.name), encoding="utf-8"
                )
            except OSError as exc:
                self._display.warning(
                    f"{role} 보안조치 보고서를 생성하지 못했습니다: {exc}"
                )
                continue
            self._display.display(
                f"보안조치 보고서 ({role}): {report_path}", color="green"
            )

    def _report_path(self, role):
        timestamp = self.started_at.strftime("%Y%m%d_%H%M%S")
        safe_role = re.sub(r"[^A-Za-z0-9_.-]+", "-", role).strip("-.") or "playbook"
        return Path(self.report_dir).expanduser() / f"REPORT.{safe_role}.{timestamp}.md"

    def _results_by_role(self):
        grouped = OrderedDict((role, []) for role in self.roles_seen)
        for role in self.roles_seen:
            if role in POLICY_CATALOGS:
                grouped[role] = self._catalog_rows(role)
        for row in self._task_rows():
            if row["role"] in POLICY_CATALOGS:
                continue
            grouped.setdefault(row["role"], []).append(row)
        return grouped

    def _task_rows(self):
        return list(self.results.values())

    def _catalog_rows(self, role):
        hosts = []
        for result_role, _policy_id, host in self.policy_results:
            if result_role == role and host not in hosts:
                hosts.append(host)
        if not hosts:
            hosts = list(self.hosts_seen or self.target_patterns or ["-"])

        rows = []
        for host in hosts:
            for policy_id, title in POLICY_CATALOGS[role].items():
                rows.append(
                    self.policy_results.get(
                        (role, policy_id, host),
                        {
                            "role": role,
                            "policy_id": policy_id,
                            "task": f"{policy_id}. {title}",
                            "host": host,
                            "changed": False,
                            "failed": False,
                            "skipped": True,
                            "warning": False,
                            "evaluated": False,
                        },
                    )
                )
        return rows

    def _needs_action(self, row):
        if row.get("policy_id"):
            return (
                row["changed"]
                or row["failed"]
                or row.get("warning", False)
                or not row.get("evaluated", False)
            )
        return row["changed"] or row["failed"]

    def _statistics(self, rows):
        needs_action = [row for row in rows if self._needs_action(row)]
        completed = [
            row
            for row in rows
            if not self._needs_action(row)
            and (row.get("policy_id") is not None or not row["skipped"])
        ]
        successful = [
            row for row in rows if row["changed"] and not row["failed"] and not row["skipped"]
        ]
        failed = [row for row in rows if row["failed"]]
        return len(rows), len(completed), len(needs_action), len(successful), len(failed)

    def _render(self, role, rows, filename):
        total, completed, needed, successful, failed = self._statistics(rows)
        inventory = ", ".join(map(str, self.inventory_sources)) or "-"
        role_hosts = list(OrderedDict.fromkeys(row["host"] for row in rows))
        targets = ", ".join(role_hosts or self.target_patterns) or "-"
        os_info = ", ".join(
            f"{host}: {self.os_by_host[host]}"
            for host in role_hosts
            if host in self.os_by_host
        ) or "-"
        started = self.started_at.strftime("%Y-%m-%d %H:%M:%S %Z")
        finished = self.finished_at.strftime("%Y-%m-%d %H:%M:%S %Z")
        apply_text = str(self.apply_policy).lower()

        lines = [
            f"# {self.report_title}",
            "",
            "## 1. 보고서 개요",
            "",
            "### 가. 보안조치 기본정보",
            "",
            "|항목|내용|",
            "|-|-|",
            f"|실행 시작시간|{_escape_cell(started)}|",
            f"|실행 종료시간|{_escape_cell(finished)}|",
            f"|조치 자동적용 여부|{apply_text}|",
            f"|실행 대상|{_escape_cell(targets)}|",
            f"|인벤토리|{_escape_cell(inventory)}|",
            f"|실행 사용자|{_escape_cell(getpass.getuser())}|",
            f"|대상 OS|{_escape_cell(os_info)}|",
            f"|Ansible playbook|{_escape_cell(self.playbook_name or '-')}|",
            f"|실행 role 목록|{_escape_cell(role)}|",
            f"|보고서 파일명|{_escape_cell(filename)}|",
            "",
            "### 나. 보안조치 통계",
            "",
        ]

        if self.apply_policy:
            lines.extend(
                [
                    "|총 검사 정책 수|조치 완료 정책 수|조치 필요 정책 수|조치 성공 정책 수|조치 실패 정책 수|",
                    "|-|-|-|-|-|",
                    f"|{total}|{completed}|{needed}|{successful}|{failed}|",
                ]
            )
        else:
            lines.extend(
                [
                    "|총 검사 정책 수|조치 완료 정책 수|조치 필요 정책 수|",
                    "|-|-|-|",
                    f"|{total}|{completed}|{needed}|",
                ]
            )

        lines.extend(["", "## 2. 정책 별 세부현황", ""])
        lines.extend(
            [
                f"### 가. {role}",
                "",
                "|조치항목 이름|조치 대상여부(true/false)|정책 적용결과(true/false)|",
                "|-|-|-|",
            ]
        )
        for row in rows:
            target = self._needs_action(row)
            applied = (
                self.apply_policy
                and row["changed"]
                and not row["failed"]
                and not row["skipped"]
            )
            display_name = f"{row['task']} ({row['host']})"
            lines.append(
                f"|{_escape_cell(display_name)}|{str(target).lower()}|"
                f"{str(applied).lower()}|"
            )
        lines.append("")

        return "\n".join(lines).rstrip() + "\n"
