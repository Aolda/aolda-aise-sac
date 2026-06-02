# storage_root_ssh

## 기능 한줄정리

Storage 호스트의 root SSH 접속과 SSH 인증 방식을 drop-in 설정으로 제한합니다.

## 적용방법

1. 기본 report로 목표 SSH 정책을 확인합니다.
2. 실제 적용은 `security_action_mode: enforce`에서 수행합니다.
3. SSH 설정 파일은 배포 전 `sshd -t`로 검증됩니다.
4. 설정 변경 시 `ssh` 서비스를 reload합니다.

## 제공인자

| 인자 | 기본값 | 설명 |
|---|---:|---|
| `enable_storage_root_ssh_restrict` | `true` | 기능 활성화 여부 |
| `storage_permit_root_login` | `no` | PermitRootLogin 값 |
| `storage_password_authentication` | `no` | PasswordAuthentication 값 |
| `storage_pubkey_authentication` | `yes` | PubkeyAuthentication 값 |
| `storage_sshd_config_path` | `/etc/ssh/sshd_config` | 기본 sshd 설정 경로 |
| `storage_sshd_dropin_path` | `/etc/ssh/sshd_config.d/99-storage-security.conf` | 관리 drop-in 경로 |

## 세부 진행단계

1. root login, password auth, pubkey auth 목표값을 report로 출력합니다.
2. enforce 모드에서 SSH drop-in 디렉터리를 생성합니다.
3. SSH 보안 설정 템플릿을 렌더링합니다.
4. `/usr/sbin/sshd -t`로 설정 문법을 검증합니다.
5. 검증 성공 시 drop-in 파일을 배포합니다.
6. 변경이 발생하면 `ssh` 서비스를 reload합니다.

## 단일기능 실행방법

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags storage_root_ssh \
  --limit storage_hosts \
  --check --diff
```

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags storage_root_ssh \
  --limit storage_hosts \
  -e "security_action_mode=enforce"
```
