# ceph_keyring

## 기능 한줄정리

Ceph keyring 파일의 존재 여부와 권한을 점검하고, 명시 모드에서 소유자/그룹/권한을 보정합니다.

## 적용방법

1. 기본값은 `ceph_keyring_report_only: true`로 점검만 수행합니다.
2. 실제 권한 적용은 `security_action_mode: enforce`와 `ceph_keyring_report_only: false`가 필요합니다.
3. 관리 대상 keyring은 `ceph_keyring_policy`에 명시합니다.

## 제공인자

| 인자 | 기본값 | 설명 |
|---|---:|---|
| `enable_ceph_keyring_hardening` | `true` | 기능 활성화 여부 |
| `ceph_admin_keyring_mode` | `0600` | admin keyring 권장 권한 |
| `ceph_service_keyring_mode` | `0640` | 서비스 keyring 권장 권한 |
| `ceph_keyring_report_only` | `true` | 점검 전용 여부 |
| `ceph_keyring_policy` | admin keyring 1개 | path/owner/group/mode 정책 목록 |

## 세부 진행단계

1. `ceph_keyring_policy`에 정의된 각 keyring 파일의 stat 정보를 조회합니다.
2. report-only 여부, 실행 모드, stat 결과를 출력합니다.
3. enforce + report_only false 조건에서 파일 소유자, 그룹, 권한을 적용합니다.
4. 존재하지 않는 파일은 Ansible file 모듈의 `state: file` 기준으로 실패하여 누락을 드러냅니다.

## 단일기능 실행방법

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags ceph_keyring \
  --limit ceph_hosts \
  --check --diff
```

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags ceph_keyring \
  --limit ceph_hosts \
  -e "security_action_mode=enforce ceph_keyring_report_only=false"
```
