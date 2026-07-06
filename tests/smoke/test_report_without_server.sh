#!/usr/bin/env bash

set -euo pipefail

project_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$project_root"

mode="${1:-localhost}"
three_column_header='|총 검사 정책 수|조치 완료 정책 수|조치 필요 정책 수|'
five_column_header='|총 검사 정책 수|조치 완료 정책 수|조치 필요 정책 수|조치 성공 정책 수|조치 실패 정책 수|'

fail() {
  echo "실패: $*" >&2
  exit 1
}

reports_after() {
  local marker="$1"
  find reports -maxdepth 1 -type f -name 'REPORT.*.md' -newer "$marker" \
    -printf '%p\n' | sort
}

assert_contains() {
  local file="$1"
  local expected="$2"
  grep -Fq "$expected" "$file" || fail "$(basename "$file")에 다음 문구가 없습니다: $expected"
}

assert_not_contains() {
  local file="$1"
  local unexpected="$2"
  if grep -Fq "$unexpected" "$file"; then
    fail "$(basename "$file")에 포함되면 안 되는 문구가 있습니다: $unexpected"
  fi
}

run_and_find_reports() {
  local marker
  local reports
  marker="$(mktemp)"
  sleep 1
  "$@" >&2
  reports="$(reports_after "$marker")"
  rm -f "$marker"
  [[ -n "$reports" ]] || fail "실행 후 Markdown 보고서가 생성되지 않았습니다."
  printf '%s\n' "$reports"
}

validate_common_report() {
  local report="$1"
  local host="$2"
  local role="$3"
  assert_contains "$report" "# 보안조치 결과 보고서"
  assert_contains "$report" "## 1. 보고서 개요"
  assert_contains "$report" "### 가. 보안조치 기본정보"
  assert_contains "$report" "### 나. 보안조치 통계"
  assert_contains "$report" "## 2. 정책 별 세부현황"
  assert_contains "$report" "|실행 role 목록|$role|"
  assert_contains "$report" "### 가. $role"
  assert_contains "$report" "($host)"
}

report_for_role() {
  local reports="$1"
  local role="$2"
  local report
  report="$(printf '%s\n' "$reports" | grep -F "/REPORT.${role}.")"
  [[ "$(printf '%s\n' "$report" | grep -c .)" -eq 1 ]] \
    || fail "$role 보고서가 정확히 1개 생성되지 않았습니다."
  printf '%s\n' "$report"
}

run_localhost_test() {
  local marker_path="/tmp/aise-report-test-check-mode-marker"
  local reports
  local report
  local application_report
  rm -f "$marker_path"
  reports="$(run_and_find_reports ./run-security-policy.sh --apply-policy=false \
    -i inventory/local-report-test.ini)"
  [[ "$(printf '%s\n' "$reports" | grep -c .)" -eq 2 ]] \
    || fail "role 2개 실행 후 보고서 2개가 생성되지 않았습니다."
  report="$(report_for_role "$reports" report-test-baseline)"
  application_report="$(report_for_role "$reports" report-test-application)"

  validate_common_report "$report" "localhost" "report-test-baseline"
  validate_common_report "$application_report" "localhost" "report-test-application"
  assert_contains "$report" "|조치 자동적용 여부|false|"
  assert_contains "$report" "$three_column_header"
  assert_not_contains "$report" "$five_column_header"
  assert_contains "$report" "(localhost)"
  [[ ! -e "$marker_path" ]] || fail "apply_policy=false인데 localhost marker가 생성되었습니다."
  echo "성공: localhost report-only smoke test ($report)"
}

docker_available() {
  command -v docker >/dev/null 2>&1 && docker info >/dev/null 2>&1
}

prepare_docker() {
  if docker inspect sac-test-ubuntu >/dev/null 2>&1; then
    docker rm -f sac-test-ubuntu >/dev/null
  fi
  docker run -dit --name sac-test-ubuntu ubuntu:24.04 sleep infinity >/dev/null
  docker exec sac-test-ubuntu bash -c \
    "apt-get update >/dev/null && DEBIAN_FRONTEND=noninteractive apt-get install -y python3 sudo >/dev/null"
}

run_docker_test() {
  local false_reports
  local true_reports
  local false_report
  local true_report
  docker_available || fail "Docker daemon을 사용할 수 없습니다."
  trap 'docker rm -f sac-test-ubuntu >/dev/null 2>&1 || true' EXIT
  prepare_docker

  false_reports="$(run_and_find_reports ./run-security-policy.sh --apply-policy=false \
    -i inventory/docker-report-test.ini)"
  [[ "$(printf '%s\n' "$false_reports" | grep -c .)" -eq 2 ]] \
    || fail "role 2개 실행 후 보고서 2개가 생성되지 않았습니다."
  false_report="$(report_for_role "$false_reports" report-test-baseline)"
  validate_common_report "$false_report" "sac-test-ubuntu" "report-test-baseline"
  assert_contains "$false_report" "|조치 자동적용 여부|false|"
  assert_contains "$false_report" "$three_column_header"
  assert_not_contains "$false_report" "$five_column_header"
  if docker exec sac-test-ubuntu test -e /tmp/aise-report-test-applied; then
    fail "apply_policy=false인데 Docker marker가 생성되었습니다."
  fi
  if docker exec sac-test-ubuntu test -e /tmp/aise-report-test-check-mode-marker; then
    fail "apply_policy=false인데 Docker check-mode marker가 생성되었습니다."
  fi

  true_reports="$(run_and_find_reports ./run-security-policy.sh --apply-policy=true \
    -i inventory/docker-report-test.ini)"
  [[ "$(printf '%s\n' "$true_reports" | grep -c .)" -eq 2 ]] \
    || fail "role 2개 실행 후 보고서 2개가 생성되지 않았습니다."
  true_report="$(report_for_role "$true_reports" report-test-application)"
  validate_common_report "$true_report" "sac-test-ubuntu" "report-test-application"
  assert_contains "$true_report" "|조치 자동적용 여부|true|"
  assert_contains "$true_report" "$five_column_header"
  docker exec sac-test-ubuntu test -e /tmp/aise-report-test-applied \
    || fail "apply_policy=true인데 Docker marker가 생성되지 않았습니다."
  echo "성공: Docker false/true smoke test ($false_report, $true_report)"
}

case "$mode" in
  localhost)
    run_localhost_test
    ;;
  docker|--docker)
    run_docker_test
    ;;
  all|--all)
    run_localhost_test
    if docker_available; then
      run_docker_test
    else
      echo "건너뜀: Docker daemon을 사용할 수 없어 Docker smoke test를 실행하지 않았습니다."
    fi
    ;;
  *)
    fail "사용법: $0 [localhost|docker|all]"
    ;;
esac
