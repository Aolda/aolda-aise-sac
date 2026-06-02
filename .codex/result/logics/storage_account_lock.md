# storage_account_lock

## 기능 한줄정리

Storage 호스트의 로그인 실패 잠금 기준을 `faillock.conf`로 관리합니다.

## 적용방법

1. 기본 report로 deny, fail_interval, unlock_time 정책을 확인합니다.
2. 실제 적용은 `security_action_mode: enforce`에서 수행합니다.
3. root 계정 적용과 관리자 그룹 예외는 별도 변수로 제어합니다.

## 제공인자

| 인자 | 기본값 | 설명 |
|---|---:|---|
| `enable_storage_account_lock` | `true` | 기능 활성화 여부 |
| `faillock_deny` | `5` | 잠금 기준 실패 횟수 |
| `faillock_fail_interval` | `900` | 실패 횟수 계산 시간 |
| `faillock_unlock_time` | `600` | 자동 잠금 해제 시간 |
| `faillock_even_deny_root` | `false` | root 계정에도 적용 여부 |
| `faillock_admin_group_exempt` | `false` | sudo 그룹 예외 여부 |
| `storage_faillock_config_path` | `/etc/security/faillock.conf` | faillock 설정 경로 |

## 세부 진행단계

1. 계정 잠금 정책값을 report로 출력합니다.
2. enforce 모드에서 `faillock.conf.j2` 템플릿을 렌더링합니다.
3. `deny`, `fail_interval`, `unlock_time` 값을 설정합니다.
4. `faillock_even_deny_root`가 true이면 root 잠금 설정을 포함합니다.
5. `faillock_admin_group_exempt`가 true이면 sudo 그룹 예외 설정을 포함합니다.
6. 설정 파일을 지정 경로에 배포합니다.

## 단일기능 실행방법

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags storage_account_lock \
  --limit storage_hosts \
  --check --diff
```

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags storage_account_lock \
  --limit storage_hosts \
  -e "security_action_mode=enforce"
```
