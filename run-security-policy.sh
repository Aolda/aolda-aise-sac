#!/usr/bin/env bash

set -euo pipefail

apply_policy=false
forward_args=()
inventory_path=""
playbook_path="playbooks/security-policy-2026.yml"

while (($# > 0)); do
  arg="$1"
  case "$arg" in
    --apply-policy=true)
      apply_policy=true
      shift
      ;;
    --apply-policy=false)
      apply_policy=false
      shift
      ;;
    --apply-policy=*)
      echo "오류: --apply-policy 값은 true 또는 false여야 합니다." >&2
      exit 2
      ;;
    -i|--inventory)
      if (($# < 2)); then
        echo "오류: $arg 뒤에 inventory 경로가 필요합니다." >&2
        exit 2
      fi
      inventory_path="$2"
      forward_args+=("$arg" "$2")
      shift 2
      ;;
    -i*)
      inventory_path="${arg#-i}"
      forward_args+=("$arg")
      shift
      ;;
    --inventory=*)
      inventory_path="${arg#--inventory=}"
      forward_args+=("$arg")
      shift
      ;;
    *)
      forward_args+=("$arg")
      shift
      ;;
  esac
done

case "$(basename -- "$inventory_path")" in
  local-report-test.ini)
    playbook_path="tests/report-validation.yml"
    if [[ "$apply_policy" == "true" ]]; then
      echo "오류: localhost 보고서 테스트에서는 --apply-policy=true를 사용할 수 없습니다." >&2
      echo "격리된 Docker inventory/docker-report-test.ini를 사용하세요." >&2
      exit 2
    fi
    ;;
  docker-report-test.ini)
    playbook_path="tests/report-validation.yml"
    ;;
esac

exec ansible-playbook "$playbook_path" \
  -e "apply_policy=${apply_policy}" \
  "${forward_args[@]}"
