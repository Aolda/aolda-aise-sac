# ceph-security-baseline

Ubuntu 24.04 Ceph 호스트의 keyring 권한, SSH key 권한, 설정 파일 권한, CephX 인증, 관리자 계정, SELinux 상태, Ceph 패치를 점검하고 선택적으로 적용하는 Ansible Role입니다.

기본값은 안전한 `report` 중심 동작입니다. 실제 권한 변경, Ceph config 변경, 관리자 계정 생성, SELinux 변경, 패키지 패치는 관련 enable 변수와 `security_action_mode: enforce`를 함께 설정해야 적용됩니다.

## 구현 task

| 파일 | 구현 내용 |
| --- | --- |
| `tasks/keyring.yml` | Ceph keyring 파일 상태를 조회하고 report합니다. `enforce` 모드와 `ceph_keyring_report_only: false` 설정 시 keyring 소유권과 권한을 적용합니다. |
| `tasks/ssh_keys.yml` | Ceph 관련 사용자의 홈 디렉터리를 조회하고 SSH 디렉터리/private key 권한을 점검합니다. `enforce` 모드에서 `.ssh` 디렉터리와 private key 권한을 조정하고, 옵션에 따라 `authorized_keys`를 관리합니다. |
| `tasks/config.yml` | Ceph 설정 파일 상태와 민감정보 패턴을 조회하고 report합니다. `enforce` 모드에서 일반 설정 파일과 민감정보 포함 파일에 서로 다른 권한을 적용합니다. |
| `tasks/auth.yml` | CephX 인증 설정을 조회하고 report합니다. 옵션에 따라 `ceph config set`으로 인증 설정을 적용하고 client keyring을 배포합니다. |
| `tasks/admin_user.yml` | Ceph 관리자 계정/그룹/sudoers 정책을 report합니다. `enforce` 모드에서 관리자 그룹과 계정을 생성하고 sudoers 파일을 배포하며, 옵션에 따라 root SSH 로그인을 제한합니다. |
| `tasks/selinux.yml` | SELinux 상태와 최근 AVC 로그를 조회하고 report합니다. 옵션에 따라 SELinux 관련 패키지를 설치하고 runtime enforcing/permissive 상태를 설정하며, 허용 시 재부팅합니다. |
| `tasks/patch.yml` | Ceph health와 패키지 후보 버전을 조회하고 report합니다. `enforce` 모드에서 health 조건을 확인한 뒤 패치 모드에 따라 Ceph 패키지를 갱신하고, 허용 시 재부팅합니다. |

## 적용이 필요한 이유

- Ceph keyring은 클러스터와 client 인증 비밀을 포함하므로 과도한 파일 권한은 클러스터 권한 탈취로 이어질 수 있습니다.
- Ceph 운영 계정의 SSH private key와 authorized_keys가 느슨하게 관리되면 노드 간 이동과 관리자 권한 접근이 노출될 수 있습니다.
- Ceph 설정 파일에 key, secret, password 성격의 값이 포함될 수 있어 파일 권한을 데이터 민감도에 맞게 조정해야 합니다.
- CephX 인증이 비활성 또는 약하게 설정되면 클러스터 통신과 client 접근 통제가 약화됩니다.
- 관리자 계정과 sudoers 정책을 명시하면 운영 권한을 추적 가능하게 관리하고 root 직접 접근을 줄일 수 있습니다.
- SELinux 상태와 AVC 로그 점검은 Ceph 프로세스 접근 통제 문제와 정책 충돌을 사전에 파악하는 데 도움이 됩니다.
- Ceph 패키지 보안 패치는 스토리지 클러스터 취약점이 데이터 손상, 권한 상승, 서비스 장애로 이어지는 위험을 낮춥니다.

## 적용 시 변경점

- `ceph_keyring_policy`에 지정된 keyring 파일의 상태가 조회되고, 조건 충족 시 소유권과 권한이 변경됩니다.
- `ceph_ssh_users`의 passwd 정보를 조회해 홈 디렉터리를 산정하고, `enforce` 모드에서 `.ssh` 디렉터리와 private key 권한이 조정됩니다.
- `ceph_manage_authorized_keys`가 true이면 `ceph_authorized_keys_policy`에 정의된 authorized_keys 내용이 배포됩니다.
- `ceph_config_files`에 지정된 파일에서 민감정보 패턴을 조회하고, 민감정보 포함 여부에 따라 `ceph_config_default_mode` 또는 `ceph_config_secret_mode`가 적용됩니다.
- `enable_cephx_enforcement`, `ceph_auth_report_only: false`, `security_action_mode: enforce` 조건에서 CephX 인증 설정이 `ceph config set`으로 적용됩니다.
- `ceph_deploy_keyrings`가 true이면 `ceph_clients`에 지정된 client keyring 파일이 배포됩니다.
- `security_action_mode: enforce`에서 Ceph 관리자 그룹과 계정이 생성되고 `ceph_admin_sudoers_path`에 sudoers 파일이 배포됩니다.
- `ceph_disable_root_ssh`가 true이면 SSH drop-in을 통해 root SSH 로그인이 제한되고 SSH 서비스가 reload됩니다.
- `enable_ceph_selinux`와 `enforce` 설정 시 SELinux 패키지 설치, runtime 상태 변경, 선택적 재부팅이 수행됩니다.
- `enable_ceph_patch`와 `enforce` 설정 시 Ceph health 기준을 확인한 뒤 패치 모드에 따라 Ceph 패키지가 갱신되고, `ceph_allow_reboot`가 true이면 재부팅이 수행될 수 있습니다.

## 변수 설명

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `security_action_mode` | `report` | Role 전체 적용 모드입니다. 기본값은 보고 전용이며 실제 변경은 `enforce` 조건에서 수행됩니다. |
| `enable_ceph_keyring_hardening` | `true` | Ceph keyring 권한 점검/적용 사용 여부입니다. |
| `ceph_admin_keyring_mode` | `0600` | 관리자 keyring 권한 의도 값입니다. 현재 기본 policy에는 직접 참조되지 않습니다. |
| `ceph_service_keyring_mode` | `0640` | 서비스/client keyring 기본 권한입니다. client keyring 배포 시 기본값으로 사용됩니다. |
| `ceph_keyring_report_only` | `true` | keyring 권한 변경을 report only로 유지할지 여부입니다. 실제 변경은 false가 필요합니다. |
| `ceph_keyring_policy` | `/etc/ceph/ceph.client.admin.keyring`, `root:root`, `0600` | 권한을 점검/적용할 keyring 파일 정책 목록입니다. |
| `enable_ceph_ssh_key_check` | `true` | Ceph 관련 사용자 SSH key 권한 점검/적용 사용 여부입니다. |
| `ceph_ssh_users` | `root`, `ceph`, `ansible` | SSH key 권한을 점검할 사용자 목록입니다. |
| `ceph_ssh_dir_mode` | `0700` | `.ssh` 디렉터리에 적용할 권한입니다. |
| `ceph_private_key_mode` | `0600` | SSH private key에 적용할 권한입니다. |
| `ceph_authorized_keys_mode` | `0600` | `authorized_keys` 파일에 적용할 권한입니다. |
| `ceph_manage_authorized_keys` | `false` | `authorized_keys` 파일을 role에서 직접 관리할지 여부입니다. |
| `ceph_purge_unmanaged_keys` | `false` | 관리되지 않는 key 제거 의도 변수입니다. 현재 task에는 purge 로직이 구현되어 있지 않습니다. |
| `ceph_authorized_keys_policy` | `{}` | 사용자별 authorized_keys 내용 목록입니다. |
| `enable_ceph_config_permission_check` | `true` | Ceph 설정 파일 권한 점검/적용 사용 여부입니다. |
| `ceph_config_files` | `/etc/ceph/ceph.conf` | 권한을 점검/적용할 Ceph 설정 파일 목록입니다. |
| `ceph_config_default_mode` | `0644` | 일반 설정 파일 권한입니다. |
| `ceph_config_secret_mode` | `0640` | 민감정보 패턴이 포함된 설정 파일 권한입니다. |
| `ceph_config_owner` | `root` | Ceph 설정 파일 소유자입니다. |
| `ceph_config_group` | `ceph` | Ceph 설정 파일 그룹입니다. |
| `ceph_config_secret_patterns` | `key`, `secret`, `password` | 민감정보 포함 여부를 판단할 패턴 목록입니다. |
| `enable_cephx_enforcement` | `false` | CephX 인증 설정 적용 사용 여부입니다. |
| `ceph_auth_cluster_required` | `cephx` | `auth_cluster_required` 목표 값입니다. |
| `ceph_auth_service_required` | `cephx` | `auth_service_required` 목표 값입니다. |
| `ceph_auth_client_required` | `cephx` | `auth_client_required` 목표 값입니다. |
| `ceph_deploy_keyrings` | `false` | client keyring 파일 배포 여부입니다. |
| `ceph_auth_report_only` | `true` | CephX 인증 설정을 report only로 유지할지 여부입니다. 실제 변경은 false가 필요합니다. |
| `ceph_clients` | `[]` | 배포할 client keyring 항목 목록입니다. `keyring`, `keyring_content`, `owner`, `group`, `mode` 값을 사용할 수 있습니다. |
| `enable_ceph_admin_user_policy` | `true` | Ceph 관리자 계정/sudoers 정책 사용 여부입니다. |
| `ceph_admin_users` | `cephadmin`, `ansible` | 생성 또는 관리할 Ceph 관리자 계정 목록입니다. |
| `ceph_admin_groups` | `sudo` | Ceph 관리자 계정에 부여할 그룹 목록입니다. |
| `ceph_admin_sudo_nopasswd` | `true` | sudoers에 NOPASSWD를 설정할지 여부입니다. |
| `ceph_admin_sudo_commands` | `ALL` | sudoers에서 허용할 명령 목록입니다. |
| `ceph_disable_root_ssh` | `false` | Ceph 호스트 root SSH 로그인을 제한할지 여부입니다. |
| `ceph_admin_sudoers_path` | `/etc/sudoers.d/90-ceph-admin-users` | Ceph 관리자 sudoers 파일 경로입니다. |
| `enable_ceph_selinux` | `false` | SELinux 설정 적용 사용 여부입니다. |
| `ceph_selinux_state` | `permissive` | 설정할 SELinux runtime 상태입니다. `permissive` 또는 `enforcing`에 대해 `setenforce`를 실행합니다. |
| `ceph_selinux_policy` | `targeted` | SELinux policy 의도 값입니다. 현재 task에서는 report용 변수입니다. |
| `ceph_selinux_install_packages` | `false` | SELinux 관련 패키지 설치 여부입니다. |
| `ceph_selinux_allow_reboot` | `false` | SELinux 설정 후 재부팅 허용 여부입니다. |
| `ceph_selinux_report_avc` | `true` | 최근 AVC 로그 조회/report 여부입니다. |
| `enable_ceph_patch` | `false` | Ceph 패키지 패치 적용 여부입니다. |
| `ceph_patch_mode` | `report` | 패치 모드입니다. `report`, `security_only`, `point_release`, `specific_version` 값을 사용합니다. |
| `ceph_target_version` | `""` | `specific_version` 모드에서 적용할 Ceph 패키지 버전입니다. |
| `ceph_patch_health_required` | `HEALTH_OK` | 패치 전 요구할 Ceph health 문자열입니다. |
| `ceph_rolling_patch` | `true` | rolling patch 의도 변수입니다. 현재 role 내부에 orchestration 로직은 구현되어 있지 않습니다. |
| `ceph_allow_reboot` | `false` | 패치 후 재부팅 필요 시 자동 재부팅 허용 여부입니다. |
| `ceph_patch_batch_size` | `1` | 패치 배치 크기 의도 변수입니다. 현재 role 내부에서는 직접 사용하지 않습니다. |
| `ceph_patch_packages` | `ceph`, `ceph-common`, `ceph-osd`, `ceph-mon`, `ceph-mgr` | 패치 조회/적용 대상 Ceph 패키지 목록입니다. |

## 실행 예시

```bash
ansible-playbook playbooks/security_baseline.yml -i inventory/hosts.yml --limit ceph_hosts
```

keyring 권한과 CephX 설정을 실제 적용하려면 inventory 또는 group vars에서 다음과 같이 명시합니다.

```yaml
security_action_mode: enforce
ceph_keyring_report_only: false
enable_cephx_enforcement: true
ceph_auth_report_only: false
```
