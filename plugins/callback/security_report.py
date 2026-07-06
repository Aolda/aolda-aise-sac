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
        for row in self._policy_rows():
            grouped.setdefault(row["role"], []).append(row)
        return grouped

    def _policy_rows(self):
        return list(self.results.values())

    @staticmethod
    def _statistics(rows):
        needs_action = [row for row in rows if row["changed"] or row["failed"]]
        completed = [
            row
            for row in rows
            if not row["changed"] and not row["failed"] and not row["skipped"]
        ]
        successful = [
            row for row in rows if row["changed"] and not row["failed"] and not row["skipped"]
        ]
        failed = [row for row in rows if row["failed"]]
        return len(rows), len(completed), len(needs_action), len(successful), len(failed)

    def _render(self, role, rows, filename):
        total, completed, needed, successful, failed = self._statistics(rows)
        inventory = ", ".join(map(str, self.inventory_sources)) or "-"
        targets = ", ".join(self.hosts_seen or self.target_patterns) or "-"
        os_info = ", ".join(
            f"{host}: {value}" for host, value in self.os_by_host.items()
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
            target = row["changed"] or row["failed"]
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
