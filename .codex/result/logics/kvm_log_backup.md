# kvm_log_backup

## 기능 한줄정리

KVM/libvirt 로그의 logrotate 정책을 관리하고, 선택적으로 로그 파일을 백업 경로에 복사합니다.

## 적용방법

1. 기본 report로 관리 대상 로그와 rotate 정책을 확인합니다.
2. 실제 logrotate 설정 배포는 `security_action_mode: enforce`에서 수행합니다.
3. 로그 백업 실행은 `kvm_log_backup_enabled: true`가 추가로 필요합니다.

## 제공인자

| 인자 | 기본값 | 설명 |
|---|---:|---|
| `enable_kvm_log_backup` | `true` | 기능 활성화 여부 |
| `kvm_log_paths` | libvirt 로그 경로 | 관리 대상 로그 |
| `kvm_log_rotate_period` | `daily` | rotate 주기 |
| `kvm_log_rotate_count` | `30` | 보관 개수 |
| `kvm_log_compress` | `true` | 압축 여부 |
| `kvm_log_copytruncate` | `true` | copytruncate 사용 여부 |
| `kvm_log_backup_enabled` | `false` | 백업 실행 여부 |
| `kvm_log_backup_dest` | `/backup/kvm-logs` | 백업 저장 경로 |
| `kvm_logrotate_config_path` | `/etc/logrotate.d/libvirt-security` | logrotate 설정 경로 |

## 세부 진행단계

1. 로그 경로, rotate 주기, 보관 개수, 압축 여부를 report로 출력합니다.
2. enforce 모드에서 logrotate 템플릿을 렌더링합니다.
3. 렌더링 결과를 `logrotate -d`로 검증합니다.
4. `kvm_log_backup_enabled`가 true이면 백업 디렉터리를 생성합니다.
5. 관리 대상 로그 glob을 순회하며 존재하는 로그 파일을 백업 디렉터리로 복사합니다.

## 단일기능 실행방법

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags kvm_log_backup \
  --limit kvm_hosts \
  --check --diff
```

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags kvm_log_backup \
  --limit kvm_hosts \
  -e "security_action_mode=enforce"
```
