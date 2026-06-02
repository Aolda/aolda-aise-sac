# storage_accounts

## 기능 한줄정리

Storage 호스트의 명시된 퇴직/불필요 계정을 report, lock, delete 모드로 관리합니다.

## 적용방법

1. 기본 report로 `storage_retired_users` 중 실제 조치 대상 계정을 확인합니다.
2. 계정 잠금은 `security_action_mode: enforce`, `storage_account_action: lock`이 필요합니다.
3. 계정 삭제는 `security_action_mode: delete`, `storage_account_action: delete`가 필요합니다.
4. 허용/제외 계정은 조치 대상에서 자동 제외됩니다.

## 제공인자

| 인자 | 기본값 | 설명 |
|---|---:|---|
| `enable_storage_account_hardening` | `true` | 기능 활성화 여부 |
| `storage_allowed_users` | root, ansible, admin, ceph | 보호할 계정 |
| `storage_retired_users` | `[]` | 퇴직/불필요 계정 |
| `storage_account_action` | `report` | `report`, `lock`, `delete` |
| `storage_nologin_shell` | `/usr/sbin/nologin` | 잠금 시 shell |
| `storage_remove_home` | `false` | 삭제 시 홈 제거 여부 |
| `storage_account_excluded_users` | ansible, ceph | 조치 제외 계정 |

## 세부 진행단계

1. `storage_retired_users`에 명시된 계정의 passwd 정보를 조회합니다.
2. retired 목록에서 allowed/excluded 목록을 제외해 실제 조치 대상을 산정합니다.
3. action, target, excluded, remove_home, mode를 report로 출력합니다.
4. enforce + lock 모드에서 대상 계정을 password lock하고 nologin shell을 적용합니다.
5. delete + delete 모드에서 대상 계정을 삭제합니다.
6. `storage_remove_home`이 true이면 삭제 시 홈 디렉터리도 제거합니다.

## 단일기능 실행방법

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags storage_accounts \
  --limit storage_hosts \
  --check --diff
```

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags storage_accounts \
  --limit storage_hosts \
  -e "security_action_mode=enforce storage_account_action=lock storage_retired_users=['olduser']"
```
