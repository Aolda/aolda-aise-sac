# storage_password_age

## 기능 한줄정리

Storage 호스트의 지정 사용자에 대해 패스워드 최대/최소 사용 기간과 만료 경고일을 관리합니다.

## 적용방법

1. 기본값은 `enable_storage_password_age: false`로 비활성입니다.
2. 기능 활성화 후 report로 대상 사용자와 현재 chage 상태를 확인합니다.
3. 기존 사용자에 실제 적용하려면 `password_age_apply_existing_users: true`와 `security_action_mode: enforce`가 필요합니다.
4. 서비스 계정은 `password_age_excluded_users`로 제외합니다.

## 제공인자

| 인자 | 기본값 | 설명 |
|---|---:|---|
| `enable_storage_password_age` | `false` | 기능 활성화 여부 |
| `password_max_days` | `90` | 최대 사용일 |
| `password_min_days` | `1` | 최소 사용일 |
| `password_warn_age` | `7` | 만료 전 경고일 |
| `password_age_target_users` | `admin`, `ansible` | 적용 대상 사용자 |
| `password_age_excluded_users` | 서비스 계정 목록 | 제외 사용자 |
| `password_age_apply_existing_users` | `false` | 기존 계정에 적용 여부 |

## 세부 진행단계

1. target 사용자 목록에서 excluded 사용자 목록을 제외해 실제 대상을 산정합니다.
2. 최대/최소 사용일, 경고일, 대상 사용자를 report로 출력합니다.
3. 대상 사용자별 `chage -l`을 실행해 현재 상태를 조회합니다.
4. enforce + apply_existing true 조건에서 `chage -M -m -W`를 실행합니다.
5. 서비스 계정은 제외 목록에 포함된 경우 조치하지 않습니다.

## 단일기능 실행방법

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags storage_password_age \
  --limit storage_hosts \
  --check --diff \
  -e "enable_storage_password_age=true"
```

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags storage_password_age \
  --limit storage_hosts \
  -e "enable_storage_password_age=true password_age_apply_existing_users=true security_action_mode=enforce"
```
