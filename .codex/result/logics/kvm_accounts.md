# kvm_accounts

## 기능 한줄정리

KVM 제어 그룹 또는 명시된 퇴직 계정 중 미사용/불필요 계정을 식별하고, 보고서 생성 또는 명시 모드에서 잠금/삭제를 수행합니다.

## 적용방법

1. 기본 점검은 별도 변경 없이 `security_action_mode: report`로 실행합니다.
2. 잠금 적용 시 `security_action_mode: enforce`, `kvm_account_action: lock`을 설정합니다.
3. 삭제 적용 시 `security_action_mode: delete`, `kvm_account_action: delete`를 설정합니다.
4. 운영 값은 `group_vars/kvm_hosts.yml` 또는 `host_vars/<hostname>.yml`에서 재정의합니다.

## 제공인자

| 인자 | 기본값 | 설명 |
|---|---:|---|
| `security_action_mode` | `report` | 실행 모드 |
| `enable_kvm_account_hardening` | `true` | 기능 활성화 여부 |
| `kvm_allowed_users` | 기본 허용 계정 목록 | 보호할 계정 목록 |
| `kvm_retired_users` | `[]` | 퇴직/불필요 계정 목록 |
| `kvm_account_action` | `report` | `report`, `lock`, `delete` |
| `kvm_nologin_shell` | `/usr/sbin/nologin` | 잠금 시 적용 shell |
| `kvm_remove_home` | `false` | 삭제 시 홈 디렉터리 제거 여부 |
| `kvm_uid_min` | `1000` | 일반 사용자 UID 기준 |
| `kvm_account_excluded_users` | `ansible`, `kolla` | 조치 제외 계정 |
| `kvm_account_report_dir` | `/tmp/kvm_audit_reports` | 보고서 저장 경로 |
| `kvm_account_inactivity_threshold_days` | `30` | 미사용 판단 기준 |
| `kvm_account_restriction_threshold_days` | `60` | 잠금 후보 기준 |
| `kvm_account_target_groups` | `kvm`, `qemu`, `libvirt` | 점검 대상 그룹 |
| `kvm_account_manual_script_enabled` | `true` | 수동 잠금 스크립트 생성 여부 |

## 세부 진행단계

1. 기존 `kvm_account_audit` 중첩 변수와 신규 defaults 변수를 호환 처리합니다.
2. 보고서 저장 디렉터리를 생성합니다.
3. `kvm`, `qemu`, `libvirt` 등 대상 그룹의 사용자 목록을 조회합니다.
4. 제외 계정과 UID 기준 미만 계정을 필터링합니다.
5. `lastlog` 기준 미사용 일수를 계산합니다.
6. `kvm_retired_users`에 명시된 계정을 별도 대상에 포함합니다.
7. 미사용/퇴직 계정 목록을 보고합니다.
8. 60일 이상 미사용 계정 중 허용/제외 계정을 뺀 잠금 후보를 산정합니다.
9. enforce + lock 모드일 때 계정을 잠그고 nologin shell을 적용합니다.
10. delete + delete 모드일 때 명시된 퇴직 계정을 삭제합니다.
11. Markdown 감사 보고서를 생성합니다.
12. 필요 시 수동 잠금 스크립트를 배포합니다.

## 단일기능 실행방법

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags kvm_accounts \
  --limit kvm_hosts \
  --check --diff
```

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags kvm_accounts \
  --limit kvm_hosts \
  -e "security_action_mode=enforce kvm_account_action=lock"
```
