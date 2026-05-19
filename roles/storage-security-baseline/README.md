# storage-security-baseline

Ubuntu 24.04 스토리지 호스트의 SSH 접근 제한, 패스워드 복잡도, 계정 잠금, 패스워드 사용 기간, 퇴직 계정 처리를 수행하는 Ansible Role입니다.

기본값은 안전한 `report` 중심 동작입니다. 실제 SSH/PAM 설정 변경과 계정 처리는 관련 enable 변수와 `security_action_mode: enforce`를 함께 설정해야 적용됩니다. 계정 삭제는 별도의 `security_action_mode: delete` 조건을 사용합니다.

## 구현 task

| 파일 | 구현 내용 |
| --- | --- |
| `tasks/root_ssh.yml` | SSH root 로그인, password authentication, pubkey authentication 정책을 report하고, `enforce` 모드에서 sshd drop-in 설정을 배포합니다. |
| `tasks/password_complexity.yml` | 패스워드 복잡도 정책을 report하고, `enforce` 모드에서 `libpam-pwquality` 패키지를 설치한 뒤 pwquality 설정 파일을 배포합니다. |
| `tasks/account_lock.yml` | faillock 계정 잠금 정책을 report하고, `enforce` 모드에서 faillock 설정 파일을 배포합니다. |
| `tasks/password_age.yml` | 대상 사용자의 `chage` 상태를 조회하고, 옵션에 따라 패스워드 최대/최소 사용 기간과 경고 기간을 적용합니다. |
| `tasks/accounts.yml` | 명시적 퇴직 계정 목록을 기준으로 허용/제외 계정을 걸러낸 뒤, `enforce` 모드에서 계정 잠금 또는 `delete` 모드에서 계정 삭제를 수행합니다. |

## 적용이 필요한 이유

- 스토리지 호스트의 root SSH 로그인과 패스워드 인증은 무차별 대입, 인증정보 탈취, 운영자 실수의 영향을 키울 수 있습니다.
- 약한 패스워드는 스토리지 관리 계정 탈취로 이어질 수 있어 최소 길이와 문자 조합 정책이 필요합니다.
- 반복 로그인 실패에 대한 계정 잠금 정책은 자동화된 인증 공격을 늦추고 이상 징후를 드러냅니다.
- 장기간 변경되지 않은 패스워드는 유출된 인증정보가 계속 유효하게 남는 위험을 키웁니다.
- 퇴직자 또는 사용 종료 계정은 스토리지 데이터 접근 권한이 남지 않도록 잠금 또는 삭제해야 합니다.

## 적용 시 변경점

- `security_action_mode: enforce`에서 SSH drop-in 파일이 `storage_sshd_dropin_path`에 생성되고 SSH 서비스가 reload됩니다.
- `libpam-pwquality` 패키지가 설치되고 `storage_pwquality_config_path`에 pwquality 설정이 배포됩니다.
- `storage_faillock_config_path`에 faillock 정책 설정이 배포됩니다.
- `enable_storage_password_age`와 `password_age_apply_existing_users`가 true이고 `enforce` 모드이면 대상 사용자에게 `chage` 정책이 적용됩니다.
- `storage_retired_users` 중 `storage_allowed_users`와 `storage_account_excluded_users`에 포함되지 않은 계정이 계정 처리 대상이 됩니다.
- `security_action_mode: enforce`와 `storage_account_action: lock`을 함께 설정하면 대상 계정의 password lock이 수행되고 shell이 `storage_nologin_shell`로 변경됩니다.
- `security_action_mode: delete`와 `storage_account_action: delete`를 함께 설정하면 대상 계정이 삭제됩니다. `storage_remove_home`이 true이면 home 디렉터리도 함께 삭제됩니다.

## 변수 설명

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `security_action_mode` | `report` | Role 전체 적용 모드입니다. 기본값은 보고 전용이며 실제 변경은 주로 `enforce` 또는 삭제용 `delete`에서 수행됩니다. |
| `enable_storage_root_ssh_restrict` | `true` | SSH root 로그인 및 인증 방식 제한 정책 사용 여부입니다. |
| `storage_permit_root_login` | `no` | 배포할 `PermitRootLogin` 값입니다. |
| `storage_password_authentication` | `no` | 배포할 `PasswordAuthentication` 값입니다. |
| `storage_pubkey_authentication` | `yes` | 배포할 `PubkeyAuthentication` 값입니다. |
| `storage_sshd_config_path` | `/etc/ssh/sshd_config` | 기본 sshd 설정 파일 경로입니다. 현재 task에서는 report용 변수입니다. |
| `storage_sshd_dropin_path` | `/etc/ssh/sshd_config.d/99-storage-security.conf` | SSH 보안 drop-in 설정 파일 경로입니다. |
| `enable_storage_password_complexity` | `true` | pwquality 기반 패스워드 복잡도 정책 사용 여부입니다. |
| `password_minlen` | `12` | 패스워드 최소 길이입니다. |
| `password_dcredit` | `-1` | 숫자 문자 요구 정책 값입니다. |
| `password_ucredit` | `-1` | 대문자 요구 정책 값입니다. |
| `password_lcredit` | `-1` | 소문자 요구 정책 값입니다. |
| `password_ocredit` | `-1` | 특수문자 요구 정책 값입니다. |
| `password_retry` | `3` | 패스워드 입력 재시도 횟수입니다. |
| `password_dictcheck` | `true` | 사전 단어 검사 사용 여부입니다. |
| `storage_pwquality_config_path` | `/etc/security/pwquality.conf.d/99-storage-security.conf` | pwquality 설정 파일 경로입니다. |
| `enable_storage_account_lock` | `true` | faillock 기반 계정 잠금 정책 사용 여부입니다. |
| `faillock_deny` | `5` | 계정 잠금 기준 실패 횟수입니다. |
| `faillock_fail_interval` | `900` | 실패 횟수 집계 시간 범위(초)입니다. |
| `faillock_unlock_time` | `600` | 계정 잠금 해제까지의 시간(초)입니다. |
| `faillock_even_deny_root` | `false` | root 계정에도 faillock 정책을 적용할지 여부입니다. |
| `faillock_admin_group_exempt` | `false` | sudo 그룹을 faillock 예외 admin group으로 둘지 여부입니다. |
| `storage_faillock_config_path` | `/etc/security/faillock.conf` | faillock 설정 파일 경로입니다. |
| `enable_storage_password_age` | `false` | 패스워드 사용 기간 정책 사용 여부입니다. |
| `password_max_days` | `90` | 패스워드 최대 사용 기간입니다. |
| `password_min_days` | `1` | 패스워드 최소 사용 기간입니다. |
| `password_warn_age` | `7` | 만료 전 경고 기간입니다. |
| `password_age_target_users` | `admin`, `ansible` | 패스워드 사용 기간 정책 대상 사용자 목록입니다. |
| `password_age_excluded_users` | `root`, `ceph`, `nova`, `cinder`, `glance` | 패스워드 사용 기간 정책에서 제외할 사용자 목록입니다. |
| `password_age_apply_existing_users` | `false` | 기존 사용자에게 `chage` 정책을 실제 적용할지 여부입니다. |
| `enable_storage_account_hardening` | `true` | 퇴직 계정 잠금/삭제 정책 사용 여부입니다. |
| `storage_allowed_users` | `root`, `ansible`, `admin`, `ceph` | 계정 처리 대상에서 제외할 허용 계정 목록입니다. |
| `storage_retired_users` | `[]` | 잠금 또는 삭제 대상으로 지정할 퇴직 계정 목록입니다. |
| `storage_account_action` | `report` | 계정 처리 방식입니다. `report`, `lock`, `delete` 값을 사용합니다. |
| `storage_nologin_shell` | `/usr/sbin/nologin` | 계정 잠금 시 적용할 shell입니다. |
| `storage_remove_home` | `false` | 계정 삭제 시 home 디렉터리도 삭제할지 여부입니다. |
| `storage_account_excluded_users` | `ansible`, `ceph` | 퇴직 계정 처리에서 제외할 사용자 목록입니다. |

## 실행 예시

```bash
ansible-playbook playbooks/security_baseline.yml -i inventory/hosts.yml --limit storage_hosts
```

SSH, pwquality, faillock 설정을 실제 적용하려면 inventory 또는 group vars에서 다음과 같이 명시합니다.

```yaml
security_action_mode: enforce
```
