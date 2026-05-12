# kvm_session_timeout

## 기능 한줄정리

KVM 호스트의 SSH idle timeout과 shell 자동 로그아웃 시간을 표준 정책으로 설정합니다.

## 적용방법

1. 기본 실행은 현재 정책값을 report로 출력합니다.
2. 실제 적용은 `security_action_mode: enforce`로 실행합니다.
3. SSH 설정은 drop-in 파일로 배포되며 `sshd -t` 검증 후 reload됩니다.
4. shell timeout은 `/etc/profile.d` 파일로 배포됩니다.

## 제공인자

| 인자 | 기본값 | 설명 |
|---|---:|---|
| `security_action_mode` | `report` | 실행 모드 |
| `enable_kvm_session_timeout` | `true` | 기능 활성화 여부 |
| `ssh_client_alive_interval` | `300` | SSH idle 확인 주기 |
| `ssh_client_alive_count_max` | `2` | SSH 응답 실패 허용 횟수 |
| `apply_shell_timeout` | `true` | shell timeout 적용 여부 |
| `shell_timeout` | `600` | shell 자동 로그아웃 시간 |
| `sshd_security_config_path` | `/etc/ssh/sshd_config.d/99-security-baseline.conf` | SSH drop-in 경로 |
| `shell_timeout_config_path` | `/etc/profile.d/security-timeout.sh` | shell timeout 파일 경로 |

## 세부 진행단계

1. SSH drop-in 디렉터리를 생성합니다.
2. enforce 모드에서 SSH timeout 설정 파일을 렌더링합니다.
3. 렌더링된 SSH 설정을 `/usr/sbin/sshd -t`로 검증합니다.
4. 설정이 변경되면 `ssh` 서비스를 reload합니다.
5. `apply_shell_timeout`이 true이면 shell timeout 스크립트를 배포합니다.
6. report 메시지로 적용 예정 값을 출력합니다.

## 단일기능 실행방법

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags kvm_session_timeout \
  --limit kvm_hosts \
  --check --diff
```

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags kvm_session_timeout \
  --limit kvm_hosts \
  -e "security_action_mode=enforce"
```
