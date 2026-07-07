# kvm-account-audit

KVM 하이퍼바이저 호스트의 미사용 계정 점검, 세션 타임아웃, 관리망 접근 제한, libvirt 기본 브리지 제한, 로그 보관, 패치 점검을 수행하는 Ansible Role입니다.

기본값은 안전한 `report` 모드입니다. 실제 계정 잠금, 방화벽 변경, SSH 설정 변경, 패키지 패치는 관련 enable 변수와 `security_action_mode: enforce`를 함께 설정해야 적용됩니다.

## 구현 task

| 파일 | 구현 내용 |
| --- | --- |
| `tasks/accounts.yml` | KVM 관련 그룹의 미사용 계정과 명시적 퇴직 계정을 조회하고, 필요 시 수동 잠금 스크립트를 생성합니다. `enforce` 모드와 `kvm_account_action: lock` 설정 시 제한 기준을 넘은 계정을 잠금 처리합니다. 실행 결과 보고서는 공통 `security_report` callback이 생성합니다. |
| `tasks/session_timeout.yml` | SSH `ClientAliveInterval`, `ClientAliveCountMax` 설정과 shell `TMOUT` 설정을 배포합니다. |
| `tasks/ip_restrict.yml` | UFW 기반으로 관리망/비상 접근 CIDR의 서비스 포트를 허용하고, 선택적으로 기본 inbound 정책을 적용합니다. |
| `tasks/default_bridge.yml` | libvirt 기본 네트워크의 autostart 해제, active network 중지, network 정의 삭제를 선택적으로 수행합니다. |
| `tasks/log_backup.yml` | libvirt 로그에 대한 logrotate 설정을 배포하고, 옵션에 따라 별도 백업 디렉터리에 로그를 복사합니다. |
| `tasks/patch.yml` | KVM 관련 패키지의 설치 가능 버전을 조회하고, `security_only`, `latest`, `specific_version` 모드에 따라 패키지를 갱신합니다. 필요 시 재부팅을 수행합니다. |

## 적용이 필요한 이유

- KVM/libvirt 관리 계정이 장기간 방치되면 퇴직자 계정, 임시 계정, 사용 목적이 끝난 운영 계정이 공격 표면으로 남을 수 있습니다.
- SSH 세션과 shell 세션 타임아웃은 방치된 터미널을 통한 비인가 조작 위험을 줄입니다.
- 하이퍼바이저 관리 포트는 지정된 관리망과 비상 접근망으로 제한해야 운영망 노출을 줄일 수 있습니다.
- libvirt 기본 NAT 브리지는 의도하지 않은 네트워크 경로를 만들 수 있어 운영 정책에 따라 비활성화가 필요합니다.
- libvirt/qemu 로그 보관과 rotation은 장애 분석, 침해 사고 추적, 디스크 사용량 통제에 필요합니다.
- KVM/qemu/libvirt 패키지 보안 패치는 가상화 계층 취약점이 게스트 또는 호스트 권한 상승으로 이어지는 위험을 낮춥니다.

## 적용 시 변경점

- `kvm_account_target_groups`에 지정된 그룹의 구성원을 조회하고, `lastlog` 기준으로 미사용 기간을 계산합니다.
- `kvm_retired_users`에 지정된 계정은 명시적 퇴직 계정으로 감사 대상에 포함됩니다.
- 감사 결과는 다른 role과 동일하게 공통 `security_report` callback을 통해 `reports/REPORT.kvm-account-audit.<timestamp>.md` 형식의 Markdown 파일로 생성됩니다.
- `kvm_account_manual_script_enabled`가 true이면 미사용 계정 수동 잠금 스크립트가 `kvm_account_manual_script_dir`에 생성됩니다.
- `security_action_mode: enforce`와 `kvm_account_action: lock`을 함께 설정하면 제한 기준 이상 미사용 계정이 잠금 처리되고 shell이 `kvm_nologin_shell`로 변경됩니다.
- `security_action_mode: delete`와 `kvm_account_action: delete`를 함께 설정하면 `kvm_retired_users` 중 허용/제외 대상이 아닌 계정이 삭제됩니다.
- `security_action_mode: enforce`에서 SSH timeout drop-in과 shell timeout profile이 배포되고 SSH 서비스가 reload됩니다.
- `enable_kvm_ip_restrict`, `security_action_mode: enforce`, `firewall_apply_mode: enforce` 설정 시 UFW 규칙과 기본 inbound 정책이 적용됩니다.
- `enable_kvm_default_bridge_disable`과 `enforce` 설정 시 libvirt 기본 네트워크의 autostart 해제, 중지, 정의 삭제가 옵션에 따라 실행됩니다.
- `enable_kvm_log_backup`과 `enforce` 설정 시 logrotate 설정이 배포되며, `kvm_log_backup_enabled`가 true이면 로그 파일이 백업 경로로 복사됩니다.
- `enable_kvm_patch`와 `enforce` 설정 시 KVM 관련 패키지가 지정된 패치 모드에 따라 갱신되고, `kvm_allow_reboot`가 true이면 재부팅이 수행될 수 있습니다.

## 변수 설명

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `security_action_mode` | `report` | Role 전체 적용 모드입니다. 기본값은 보고 전용이며 실제 변경은 주로 `enforce` 또는 삭제용 `delete`에서 수행됩니다. |
| `enable_kvm_account_hardening` | `true` | KVM 계정 감사와 계정 잠금/삭제 정책 사용 여부입니다. |
| `kvm_allowed_users` | `root`, `ansible`, `kolla`, `ceph`, `nova`, `libvirt-qemu` | 잠금/삭제 대상에서 제외할 허용 계정 목록입니다. |
| `kvm_retired_users` | `[]` | 명시적으로 퇴직 또는 폐기 대상으로 간주할 계정 목록입니다. |
| `kvm_account_action` | `report` | 계정 처리 방식입니다. `report`, `lock`, `delete` 값을 사용합니다. |
| `kvm_nologin_shell` | `/usr/sbin/nologin` | 계정 잠금 처리 시 적용할 shell입니다. |
| `kvm_remove_home` | `false` | 계정 삭제 시 home 디렉터리도 함께 삭제할지 여부입니다. |
| `kvm_uid_min` | `1000` | 일반 사용자 계정으로 간주할 최소 UID입니다. `root`는 예외 처리됩니다. |
| `kvm_account_excluded_users` | `ansible`, `kolla` | 감사/조치 대상에서 제외할 계정 목록입니다. |
| `kvm_account_inactivity_threshold_days` | `30` | 미사용 계정으로 보고서에 포함할 기준 일수입니다. |
| `kvm_account_restriction_threshold_days` | `60` | 자동 잠금 후보로 산정할 미사용 기준 일수입니다. |
| `kvm_account_target_groups` | `kvm`, `qemu`, `libvirt` | 계정 감사를 수행할 KVM 관련 그룹 목록입니다. |
| `kvm_account_action_log_path` | `/var/log/kvm_account_audit_actions.log` | 수동 잠금 스크립트가 조치 이력을 남기는 로그 경로입니다. |
| `kvm_account_manual_script_enabled` | `true` | 수동 계정 잠금 스크립트 생성 여부입니다. |
| `kvm_account_manual_script_dir` | `/tmp` | 수동 계정 잠금 스크립트 생성 디렉터리입니다. |
| `enable_kvm_session_timeout` | `true` | SSH 및 shell 세션 timeout 설정 사용 여부입니다. |
| `ssh_client_alive_interval` | `300` | SSH idle 감지 interval 값입니다. |
| `ssh_client_alive_count_max` | `2` | SSH client alive 실패 허용 횟수입니다. |
| `apply_shell_timeout` | `true` | shell `TMOUT` 설정 적용 여부입니다. |
| `shell_timeout` | `600` | shell idle timeout 초 단위 값입니다. |
| `sshd_security_config_path` | `/etc/ssh/sshd_config.d/99-security-baseline.conf` | SSH timeout drop-in 설정 파일 경로입니다. |
| `shell_timeout_config_path` | `/etc/profile.d/security-timeout.sh` | shell timeout profile 파일 경로입니다. |
| `enable_kvm_ip_restrict` | `false` | KVM 관리 포트 접근 제한 사용 여부입니다. |
| `firewall_backend` | `ufw` | 방화벽 backend입니다. 현재 enforce 구현은 UFW만 지원합니다. |
| `firewall_apply_mode` | `report` | 방화벽 적용 모드입니다. 실제 UFW 변경은 `enforce`일 때 수행됩니다. |
| `allowed_management_cidrs` | `10.0.0.0/24` | 관리 접근을 허용할 CIDR 목록입니다. |
| `emergency_access_cidrs` | `[]` | 장애 대응용 비상 접근 CIDR 목록입니다. |
| `allowed_service_ports` | SSH 22/tcp | 관리망에서 허용할 서비스 포트 목록입니다. |
| `default_inbound_policy` | `deny` | UFW 기본 inbound 정책 값입니다. |
| `enable_default_deny` | `false` | UFW 기본 inbound 정책 적용 여부입니다. |
| `enable_kvm_default_bridge_disable` | `false` | libvirt default network 제한 정책 사용 여부입니다. |
| `kvm_libvirt_default_network_name` | `default` | 제어할 libvirt network 이름입니다. |
| `kvm_disable_network_autostart` | `true` | default network autostart 해제 여부입니다. |
| `kvm_destroy_active_network` | `false` | active 상태의 default network 중지 여부입니다. |
| `kvm_undefine_default_network` | `false` | default network 정의 삭제 여부입니다. |
| `kvm_default_bridge_action` | `report` | default bridge 처리 방식입니다. `disable`, `destroy`, `undefine` 값과 함께 사용합니다. |
| `enable_kvm_log_backup` | `true` | KVM/libvirt 로그 rotation 및 백업 정책 사용 여부입니다. |
| `kvm_log_paths` | `/var/log/libvirt/*.log`, `/var/log/libvirt/qemu/*.log` | rotation 및 백업 대상 로그 경로입니다. |
| `kvm_log_rotate_period` | `daily` | logrotate 주기입니다. |
| `kvm_log_rotate_count` | `30` | 보관할 rotation 개수입니다. |
| `kvm_log_compress` | `true` | rotation 로그 압축 여부입니다. |
| `kvm_log_copytruncate` | `true` | logrotate `copytruncate` 사용 여부입니다. |
| `kvm_log_backup_enabled` | `false` | 로그 파일 별도 백업 실행 여부입니다. |
| `kvm_log_backup_dest` | `/backup/kvm-logs` | 로그 백업 대상 디렉터리입니다. |
| `kvm_logrotate_config_path` | `/etc/logrotate.d/libvirt-security` | libvirt 로그 rotation 설정 파일 경로입니다. |
| `enable_kvm_patch` | `false` | KVM 관련 패키지 패치 적용 여부입니다. |
| `kvm_patch_mode` | `report` | 패치 모드입니다. `report`, `security_only`, `latest`, `specific_version` 값을 사용합니다. |
| `kvm_patch_packages` | `qemu-system`, `libvirt-daemon-system`, `libvirt-clients` | 패치 조회/적용 대상 패키지 목록입니다. |
| `kvm_target_package_versions` | `{}` | `specific_version` 모드에서 적용할 패키지별 버전 매핑입니다. |
| `kvm_allow_reboot` | `false` | 패치 후 재부팅 필요 시 자동 재부팅 허용 여부입니다. |
| `kvm_drain_compute_before_patch` | `true` | compute drain 의도 표시 변수입니다. 현재 task에는 실제 drain 절차가 구현되어 있지 않습니다. |
| `kvm_patch_batch_size` | `1` | 패치 배치 크기 의도 표시 변수입니다. 현재 role 내부에서는 직접 사용하지 않습니다. |

## 실행 예시

```bash
ansible-playbook playbooks/kvm_account_audit.yml -i inventory/hosts.yml
```

계정 잠금까지 적용하려면 inventory 또는 group vars에서 다음과 같이 명시합니다.

```yaml
security_action_mode: enforce
kvm_account_action: lock
```
