# Ansible 기반 SaC 보안조치 구현 가이드  
## 정책값 변경 가능 항목 및 변경 방법 보강본

---

## 0. 문서 목적

본 문서는 인프라 환경 보안조치를 Ansible 기반 SaC(Security as Code)로 구현하기 위한 절차 중심 가이드이다.

이번 보강본은 다음 요구사항을 반영한다.

1. 보안정책 변화에 따라 각 보안정책 단위별로 변경 가능한 값의 종류를 정의한다.
2. 해당 값을 어디에서, 어떤 방식으로 변경해야 하는지 정의한다.
3. 코딩 에이전트가 Ansible Role 구현 시 하드코딩하지 말아야 할 값을 명확히 한다.
4. 정책 변경 후 적용·검증 절차를 표준화한다.

---

# 1. 공통 정책값 관리 원칙

## 1.1 핵심 원칙

모든 보안정책 값은 Ansible Task 내부에 직접 하드코딩하지 않는다.

다음 값들은 반드시 변수화한다.

1. 정책 적용 여부
2. 적용 대상 계정
3. 제외 대상 계정
4. 허용 IP 대역
5. 허용 포트
6. 파일 경로
7. 파일 권한
8. 파일 소유자
9. timeout 값
10. 패스워드 복잡도 값
11. 계정 잠금 기준
12. 패치 대상 패키지
13. 패치 방식
14. SELinux 상태
15. 삭제 여부
16. 재부팅 허용 여부
17. 보고 모드 여부
18. 롤백 가능 여부

---

## 1.2 정책값 저장 위치

정책값은 다음 우선순위로 관리한다.

```text
roles/security_baseline/defaults/main.yml
group_vars/all/security_baseline.yml
group_vars/kvm_hosts/security_baseline.yml
group_vars/ceph_hosts/security_baseline.yml
group_vars/storage_hosts/security_baseline.yml
host_vars/<hostname>.yml
```

| 위치 | 용도 |
|---|---|
| `defaults/main.yml` | Role 기본 정책값 |
| `group_vars/all/security_baseline.yml` | 전체 공통 정책값 |
| `group_vars/kvm_hosts/security_baseline.yml` | KVM 노드 전용 정책값 |
| `group_vars/ceph_hosts/security_baseline.yml` | Ceph 노드 전용 정책값 |
| `group_vars/storage_hosts/security_baseline.yml` | Storage 노드 전용 정책값 |
| `host_vars/<hostname>.yml` | 특정 호스트 예외 정책값 |

---

## 1.3 공통 실행 모드

모든 보안정책은 다음 실행 모드를 지원하도록 구현한다.

```yaml
security_action_mode: report
```

| 값 | 의미 |
|---|---|
| `report` | 점검만 수행하고 변경하지 않음 |
| `enforce` | 정책값에 따라 실제 설정 변경 |
| `delete` | 계정 삭제, 네트워크 삭제 등 파괴적 작업 포함 |
| `rollback` | 사전에 정의된 롤백 정책 수행 |

구현 시 위험도가 높은 조치는 기본값을 `report` 또는 `false`로 둔다.

---

## 1.4 정책값 변경 공통 절차

정책값 변경은 다음 순서로 수행한다.

1. 변경 대상 보안정책 항목을 확인한다.
2. 해당 항목의 변수명을 확인한다.
3. 공통 정책이면 `group_vars/all/security_baseline.yml`을 수정한다.
4. 노드 그룹별 정책이면 `group_vars/<group>/security_baseline.yml`을 수정한다.
5. 특정 노드 예외 정책이면 `host_vars/<hostname>.yml`을 수정한다.
6. YAML 문법을 확인한다.

   ```bash
   ansible-playbook -i inventories/prod/hosts.ini site.yml --syntax-check
   ```

7. check mode로 변경 예상 결과를 확인한다.

   ```bash
   ansible-playbook -i inventories/prod/hosts.ini site.yml --check --diff
   ```

8. 테스트 노드에 먼저 적용한다.

   ```bash
   ansible-playbook -i inventories/prod/hosts.ini site.yml --limit test_hosts
   ```

9. 조치별 검증 명령을 수행한다.
10. 운영 노드에 순차 적용한다.
11. 변경 전후 결과를 증적으로 저장한다.

---

## 1.5 일회성 정책값 변경 방법

임시 테스트 또는 긴급 변경은 `--extra-vars`로 수행할 수 있다.

```bash
ansible-playbook -i inventories/prod/hosts.ini site.yml \
  --tags kvm_session_timeout \
  -e "ssh_client_alive_interval=600 ssh_client_alive_count_max=2"
```

외부 정책 파일을 지정할 수도 있다.

```bash
ansible-playbook -i inventories/prod/hosts.ini site.yml \
  -e @policy_override.yml
```

단, 운영 정책으로 확정된 값은 반드시 `group_vars` 또는 `host_vars`에 반영한다.

---

# 2. 공통 Enable Flag

각 보안정책은 개별적으로 활성화·비활성화할 수 있어야 한다.

```yaml
# KVM
enable_kvm_account_hardening: true
enable_kvm_session_timeout: true
enable_kvm_ip_restrict: false
enable_kvm_default_bridge_disable: false
enable_kvm_log_backup: true
enable_kvm_patch: false

# Ceph
enable_ceph_keyring_hardening: true
enable_ceph_ssh_key_check: true
enable_ceph_config_permission_check: true
enable_cephx_enforcement: false
enable_ceph_admin_user_policy: true
enable_ceph_selinux: false
enable_ceph_patch: false

# Storage
enable_storage_root_ssh_restrict: true
enable_storage_password_complexity: true
enable_storage_account_lock: true
enable_storage_password_age: false
enable_storage_account_hardening: true
```

---

# 3. KVM 보안정책

---

## 3.1 KVM - 불필요한 계정 제거

### 정책 판단

불필요한 계정 제거는 타당하다.  
단, 운영 계정이나 자동화 계정을 실수로 삭제하지 않도록 삭제보다 비활성화를 우선한다.

---

### 변경 가능한 정책값

| 변수명 | 타입 | 허용값 예시 | 설명 |
|---|---|---|---|
| `enable_kvm_account_hardening` | boolean | `true`, `false` | KVM 계정 정리 정책 활성화 여부 |
| `kvm_allowed_users` | list | 계정명 목록 | 유지할 계정 목록 |
| `kvm_retired_users` | list | 계정명 목록 | 비활성화 또는 삭제 대상 계정 |
| `kvm_account_action` | string | `report`, `lock`, `delete` | 계정 처리 방식 |
| `kvm_nologin_shell` | string | `/usr/sbin/nologin` | 잠금 시 적용할 shell |
| `kvm_remove_home` | boolean | `true`, `false` | 계정 삭제 시 홈 디렉터리 삭제 여부 |
| `kvm_uid_min` | integer | `1000` | 점검 대상 일반 사용자 UID 기준 |
| `kvm_account_excluded_users` | list | 계정명 목록 | 조치 제외 계정 |

---

### 기본값 예시

```yaml
enable_kvm_account_hardening: true

kvm_allowed_users:
  - root
  - ansible
  - kolla
  - ceph
  - nova
  - libvirt-qemu

kvm_retired_users: []

kvm_account_action: report
kvm_nologin_shell: /usr/sbin/nologin
kvm_remove_home: false
kvm_uid_min: 1000

kvm_account_excluded_users:
  - ansible
  - kolla
```

---

### 정책값 변경 방법

1. 유지할 계정이 추가되면 `kvm_allowed_users`에 계정을 추가한다.
2. 비활성화 대상 계정이 생기면 `kvm_retired_users`에 계정을 추가한다.
3. 점검만 수행하려면 `kvm_account_action: report`로 설정한다.
4. 계정 잠금을 수행하려면 `kvm_account_action: lock`으로 설정한다.
5. 계정 삭제까지 수행하려면 `kvm_account_action: delete`로 설정한다.
6. 홈 디렉터리까지 삭제하려면 `kvm_remove_home: true`로 설정한다.
7. 적용 전 check mode를 실행한다.

   ```bash
   ansible-playbook -i inventories/prod/hosts.ini site.yml \
     --tags kvm_accounts \
     --check --diff
   ```

8. 테스트 노드에 먼저 적용한다.

   ```bash
   ansible-playbook -i inventories/prod/hosts.ini site.yml \
     --tags kvm_accounts \
     --limit test_hosts
   ```

---

## 3.2 KVM - Session Timeout 설정

### 정책 판단

장시간 유지되는 관리 세션은 세션 탈취 및 무단 명령 실행 위험이 있으므로 timeout 정책 적용은 타당하다.

---

### 변경 가능한 정책값

| 변수명 | 타입 | 허용값 예시 | 설명 |
|---|---|---|---|
| `enable_kvm_session_timeout` | boolean | `true`, `false` | 세션 timeout 정책 활성화 여부 |
| `ssh_client_alive_interval` | integer | `300`, `600` | SSH idle 확인 주기 |
| `ssh_client_alive_count_max` | integer | `1`, `2`, `3` | 응답 실패 허용 횟수 |
| `apply_shell_timeout` | boolean | `true`, `false` | Shell timeout 적용 여부 |
| `shell_timeout` | integer | `600`, `900` | Shell 자동 로그아웃 시간 |
| `sshd_security_config_path` | string | `/etc/ssh/sshd_config.d/99-security-baseline.conf` | SSH 보안 설정 파일 경로 |
| `shell_timeout_config_path` | string | `/etc/profile.d/security-timeout.sh` | Shell timeout 설정 파일 경로 |

---

### 기본값 예시

```yaml
enable_kvm_session_timeout: true

ssh_client_alive_interval: 300
ssh_client_alive_count_max: 2

apply_shell_timeout: true
shell_timeout: 600

sshd_security_config_path: /etc/ssh/sshd_config.d/99-security-baseline.conf
shell_timeout_config_path: /etc/profile.d/security-timeout.sh
```

---

### 정책값 변경 방법

1. SSH 세션 유지 시간을 늘리려면 `ssh_client_alive_interval` 값을 증가시킨다.
2. SSH 세션을 더 빠르게 종료하려면 `ssh_client_alive_interval` 값을 감소시킨다.
3. 허용 실패 횟수를 조정하려면 `ssh_client_alive_count_max`를 변경한다.
4. Shell timeout을 비활성화하려면 `apply_shell_timeout: false`로 설정한다.
5. Shell timeout 시간을 변경하려면 `shell_timeout` 값을 수정한다.
6. 설정 파일 경로를 변경하려면 `sshd_security_config_path` 또는 `shell_timeout_config_path`를 수정한다.
7. 변경 후 SSH 문법 검사를 수행한다.

   ```bash
   sshd -t
   ```

8. Ansible 적용 전 check mode를 수행한다.

   ```bash
   ansible-playbook -i inventories/prod/hosts.ini site.yml \
     --tags kvm_session_timeout \
     --check --diff
   ```

---

## 3.3 KVM - IP 접근 제한 설정

### 정책 판단

관리 포트 노출을 줄이기 위한 IP 접근 제한은 타당하다.  
단, OpenStack, Ceph, Kolla 통신에 영향을 줄 수 있으므로 기본값은 비활성화하고 테스트 후 적용한다.

---

### 변경 가능한 정책값

| 변수명 | 타입 | 허용값 예시 | 설명 |
|---|---|---|---|
| `enable_kvm_ip_restrict` | boolean | `true`, `false` | IP 접근 제한 활성화 여부 |
| `firewall_backend` | string | `ufw`, `firewalld`, `nftables`, `iptables` | 사용할 방화벽 도구 |
| `allowed_management_cidrs` | list | CIDR 목록 | SSH 접근 허용 관리망 |
| `emergency_access_cidrs` | list | CIDR 목록 | 긴급 복구용 허용망 |
| `allowed_service_ports` | list | 포트 정책 목록 | 허용할 서비스 포트 |
| `default_inbound_policy` | string | `allow`, `deny` | 기본 inbound 정책 |
| `enable_default_deny` | boolean | `true`, `false` | 기본 차단 정책 적용 여부 |
| `firewall_apply_mode` | string | `report`, `enforce` | 방화벽 적용 방식 |

---

### 기본값 예시

```yaml
enable_kvm_ip_restrict: false

firewall_backend: ufw
firewall_apply_mode: report

allowed_management_cidrs:
  - 10.0.0.0/24

emergency_access_cidrs: []

allowed_service_ports:
  - port: 22
    proto: tcp
    source: management
    description: SSH management access

default_inbound_policy: deny
enable_default_deny: false
```

---

### 정책값 변경 방법

1. 관리망 대역이 변경되면 `allowed_management_cidrs`를 수정한다.
2. 긴급 접속 대역이 필요하면 `emergency_access_cidrs`에 CIDR을 추가한다.
3. 새 서비스 포트를 허용하려면 `allowed_service_ports`에 항목을 추가한다.
4. 방화벽 도구를 변경하려면 `firewall_backend`를 수정한다.
5. 점검만 수행하려면 `firewall_apply_mode: report`로 설정한다.
6. 실제 적용하려면 `firewall_apply_mode: enforce`로 설정한다.
7. 기본 차단 정책은 검증 후 `enable_default_deny: true`로 설정한다.
8. 반드시 테스트 노드에 먼저 적용한다.

   ```bash
   ansible-playbook -i inventories/prod/hosts.ini site.yml \
     --tags kvm_ip_restrict \
     --limit test_hosts
   ```

9. SSH, OpenStack API, Ceph 통신을 검증한 후 운영 노드에 확대한다.

---

## 3.4 KVM - Default Bridge 제거

### 정책 판단

OpenStack Neutron 기반 환경에서 libvirt default bridge가 불필요하다면 제거 또는 비활성화가 타당하다.

---

### 변경 가능한 정책값

| 변수명 | 타입 | 허용값 예시 | 설명 |
|---|---|---|---|
| `enable_kvm_default_bridge_disable` | boolean | `true`, `false` | default bridge 비활성화 여부 |
| `kvm_libvirt_default_network_name` | string | `default` | 대상 libvirt network 이름 |
| `kvm_disable_network_autostart` | boolean | `true`, `false` | autostart 해제 여부 |
| `kvm_destroy_active_network` | boolean | `true`, `false` | active network 중지 여부 |
| `kvm_undefine_default_network` | boolean | `true`, `false` | network 정의 삭제 여부 |
| `kvm_default_bridge_action` | string | `report`, `disable`, `destroy`, `undefine` | 처리 방식 |

---

### 기본값 예시

```yaml
enable_kvm_default_bridge_disable: false

kvm_libvirt_default_network_name: default
kvm_disable_network_autostart: true
kvm_destroy_active_network: false
kvm_undefine_default_network: false

kvm_default_bridge_action: report
```

---

### 정책값 변경 방법

1. 대상 network 이름이 다르면 `kvm_libvirt_default_network_name`을 변경한다.
2. 상태 점검만 수행하려면 `kvm_default_bridge_action: report`로 설정한다.
3. autostart만 해제하려면 `kvm_default_bridge_action: disable`로 설정한다.
4. active network까지 중지하려면 `kvm_default_bridge_action: destroy`로 설정한다.
5. 정의까지 삭제하려면 `kvm_default_bridge_action: undefine`으로 설정한다.
6. 삭제 전 `virsh net-list --all` 결과를 확인한다.
7. 적용 후 `virbr0` 제거 여부를 확인한다.

---

## 3.5 KVM - 로그 정기 관리 및 백업

### 정책 판단

KVM/libvirt 로그는 장애 분석, 침해사고 조사, 감사 증적 확보에 필요하므로 정기 관리와 백업이 타당하다.

---

### 변경 가능한 정책값

| 변수명 | 타입 | 허용값 예시 | 설명 |
|---|---|---|---|
| `enable_kvm_log_backup` | boolean | `true`, `false` | 로그 관리 정책 활성화 여부 |
| `kvm_log_paths` | list | 경로 목록 | 관리 대상 로그 경로 |
| `kvm_log_rotate_period` | string | `daily`, `weekly`, `monthly` | logrotate 주기 |
| `kvm_log_rotate_count` | integer | `30`, `90` | 보관 개수 |
| `kvm_log_compress` | boolean | `true`, `false` | 압축 여부 |
| `kvm_log_copytruncate` | boolean | `true`, `false` | copytruncate 사용 여부 |
| `kvm_log_backup_enabled` | boolean | `true`, `false` | 원격 백업 여부 |
| `kvm_log_backup_dest` | string | `/backup/kvm-logs` | 백업 저장 경로 |

---

### 기본값 예시

```yaml
enable_kvm_log_backup: true

kvm_log_paths:
  - /var/log/libvirt/*.log
  - /var/log/libvirt/qemu/*.log

kvm_log_rotate_period: daily
kvm_log_rotate_count: 30
kvm_log_compress: true
kvm_log_copytruncate: true

kvm_log_backup_enabled: false
kvm_log_backup_dest: /backup/kvm-logs
```

---

### 정책값 변경 방법

1. 관리 대상 로그가 추가되면 `kvm_log_paths`에 경로를 추가한다.
2. 보존 기간을 늘리려면 `kvm_log_rotate_count`를 증가시킨다.
3. 주기를 변경하려면 `kvm_log_rotate_period`를 변경한다.
4. 로그 압축을 비활성화하려면 `kvm_log_compress: false`로 설정한다.
5. 원격 백업을 활성화하려면 `kvm_log_backup_enabled: true`로 설정한다.
6. 백업 경로를 변경하려면 `kvm_log_backup_dest`를 수정한다.
7. 적용 전 logrotate dry-run을 수행한다.

   ```bash
   logrotate -d /etc/logrotate.d/libvirt-security
   ```

---

## 3.6 KVM - 최신 보안 패치 적용

### 정책 판단

KVM/QEMU/libvirt 보안 패치는 필요하지만 OpenStack Nova와 연동되므로 단계 적용해야 한다.

---

### 변경 가능한 정책값

| 변수명 | 타입 | 허용값 예시 | 설명 |
|---|---|---|---|
| `enable_kvm_patch` | boolean | `true`, `false` | KVM 패치 활성화 여부 |
| `kvm_patch_mode` | string | `report`, `security_only`, `latest`, `specific_version` | 패치 방식 |
| `kvm_patch_packages` | list | 패키지 목록 | 패치 대상 패키지 |
| `kvm_target_package_versions` | dict | 패키지:버전 | 특정 버전 고정 |
| `kvm_allow_reboot` | boolean | `true`, `false` | 재부팅 허용 여부 |
| `kvm_drain_compute_before_patch` | boolean | `true`, `false` | 패치 전 compute drain 여부 |
| `kvm_patch_batch_size` | integer | `1`, `2` | 한 번에 패치할 노드 수 |

---

### 기본값 예시

```yaml
enable_kvm_patch: false

kvm_patch_mode: report

kvm_patch_packages:
  - qemu-system
  - libvirt-daemon-system
  - libvirt-clients

kvm_target_package_versions: {}

kvm_allow_reboot: false
kvm_drain_compute_before_patch: true
kvm_patch_batch_size: 1
```

---

### 정책값 변경 방법

1. 패치 대상 패키지를 추가하려면 `kvm_patch_packages`에 추가한다.
2. 보안 패치만 적용하려면 `kvm_patch_mode: security_only`로 설정한다.
3. 최신 버전으로 올리려면 `kvm_patch_mode: latest`로 설정한다.
4. 특정 버전을 지정하려면 `kvm_patch_mode: specific_version`으로 설정하고 `kvm_target_package_versions`를 작성한다.
5. 재부팅을 허용하려면 `kvm_allow_reboot: true`로 설정한다.
6. 운영 노드는 `kvm_patch_batch_size: 1`로 순차 적용한다.
7. 패치 전 compute disable 또는 migration 절차를 수행한다.

---

# 4. Ceph 보안정책

---

## 4.1 Ceph - Keyring 파일 권한 관리

### 정책 판단

Ceph keyring은 클러스터 접근 인증정보이므로 소유자와 권한 관리가 필요하다.

---

### 변경 가능한 정책값

| 변수명 | 타입 | 허용값 예시 | 설명 |
|---|---|---|---|
| `enable_ceph_keyring_hardening` | boolean | `true`, `false` | keyring 권한 강화 여부 |
| `ceph_keyring_policy` | list | path, owner, group, mode | keyring별 정책 |
| `ceph_admin_keyring_mode` | string | `0600` | admin keyring 기본 권한 |
| `ceph_service_keyring_mode` | string | `0640` | 서비스 keyring 기본 권한 |
| `ceph_keyring_report_only` | boolean | `true`, `false` | 점검만 수행 여부 |

---

### 기본값 예시

```yaml
enable_ceph_keyring_hardening: true

ceph_admin_keyring_mode: "0600"
ceph_service_keyring_mode: "0640"
ceph_keyring_report_only: false

ceph_keyring_policy:
  - path: /etc/ceph/ceph.client.admin.keyring
    owner: root
    group: root
    mode: "0600"
```

---

### 정책값 변경 방법

1. 새 keyring이 추가되면 `ceph_keyring_policy`에 항목을 추가한다.
2. admin keyring 권한을 강화하려면 `mode: "0600"`으로 설정한다.
3. 서비스 계정이 읽어야 하는 keyring은 group과 mode를 함께 조정한다.
4. 점검만 수행하려면 `ceph_keyring_report_only: true`로 설정한다.
5. 적용 후 권한을 확인한다.

   ```bash
   stat -c "%U %G %a %n" /etc/ceph/*.keyring
   ```

---

## 4.2 Ceph - SSH 인증키 파일 관리

### 정책 판단

Ceph 관리용 SSH key는 노드 관리에 사용되므로 권한과 배포 범위 통제가 필요하다.

---

### 변경 가능한 정책값

| 변수명 | 타입 | 허용값 예시 | 설명 |
|---|---|---|---|
| `enable_ceph_ssh_key_check` | boolean | `true`, `false` | SSH key 점검 여부 |
| `ceph_ssh_users` | list | 사용자 목록 | 점검 대상 사용자 |
| `ceph_ssh_dir_mode` | string | `0700` | `.ssh` 디렉터리 권한 |
| `ceph_private_key_mode` | string | `0600`, `0400` | private key 권한 |
| `ceph_authorized_keys_mode` | string | `0600` | authorized_keys 권한 |
| `ceph_manage_authorized_keys` | boolean | `true`, `false` | authorized_keys 관리 여부 |
| `ceph_purge_unmanaged_keys` | boolean | `true`, `false` | 미승인 key 제거 여부 |

---

### 기본값 예시

```yaml
enable_ceph_ssh_key_check: true

ceph_ssh_users:
  - root
  - ceph
  - ansible

ceph_ssh_dir_mode: "0700"
ceph_private_key_mode: "0600"
ceph_authorized_keys_mode: "0600"

ceph_manage_authorized_keys: false
ceph_purge_unmanaged_keys: false
```

---

### 정책값 변경 방법

1. 점검 대상 계정이 추가되면 `ceph_ssh_users`에 추가한다.
2. private key 권한을 더 강화하려면 `ceph_private_key_mode: "0400"`으로 변경한다.
3. authorized_keys를 Ansible로 완전 관리하려면 `ceph_manage_authorized_keys: true`로 설정한다.
4. 미승인 키를 자동 삭제하려면 `ceph_purge_unmanaged_keys: true`로 설정한다.
5. 단, 키 자동 삭제는 접속 장애 위험이 있으므로 반드시 테스트 후 적용한다.

---

## 4.3 Ceph - ceph.conf 권한 관리

### 정책 판단

`ceph.conf`는 내부 구성 정보를 포함할 수 있으므로 권한 점검이 필요하다.  
secret 포함 여부에 따라 권한 기준을 달리해야 한다.

---

### 변경 가능한 정책값

| 변수명 | 타입 | 허용값 예시 | 설명 |
|---|---|---|---|
| `enable_ceph_config_permission_check` | boolean | `true`, `false` | ceph.conf 권한 점검 여부 |
| `ceph_config_files` | list | 파일 경로 목록 | 점검 대상 설정 파일 |
| `ceph_config_default_mode` | string | `0644` | 일반 설정 파일 권한 |
| `ceph_config_secret_mode` | string | `0640`, `0600` | 민감정보 포함 시 권한 |
| `ceph_config_secret_patterns` | list | 문자열 패턴 목록 | 민감정보 탐지 기준 |
| `ceph_config_owner` | string | `root` | 파일 소유자 |
| `ceph_config_group` | string | `root`, `ceph` | 파일 그룹 |

---

### 기본값 예시

```yaml
enable_ceph_config_permission_check: true

ceph_config_files:
  - /etc/ceph/ceph.conf

ceph_config_default_mode: "0644"
ceph_config_secret_mode: "0640"

ceph_config_owner: root
ceph_config_group: ceph

ceph_config_secret_patterns:
  - key
  - secret
  - password
```

---

### 정책값 변경 방법

1. 관리 대상 설정 파일이 추가되면 `ceph_config_files`에 추가한다.
2. 민감정보 탐지 기준을 바꾸려면 `ceph_config_secret_patterns`를 수정한다.
3. 일반 설정 파일 권한 기준을 바꾸려면 `ceph_config_default_mode`를 수정한다.
4. 민감정보 포함 파일의 권한을 강화하려면 `ceph_config_secret_mode`를 `0600`으로 변경한다.
5. 서비스 계정 접근이 필요하면 `ceph_config_group`을 해당 그룹으로 변경한다.

---

## 4.4 Ceph - CephX 인증 적용

### 정책 판단

CephX 미적용 상태라면 중대 위험으로 관리해야 한다.  
단, OpenStack 연동 영향이 있으므로 기본값은 점검 모드로 둔다.

---

### 변경 가능한 정책값

| 변수명 | 타입 | 허용값 예시 | 설명 |
|---|---|---|---|
| `enable_cephx_enforcement` | boolean | `true`, `false` | CephX 강제 적용 여부 |
| `ceph_auth_cluster_required` | string | `cephx`, `none` | cluster 인증 요구값 |
| `ceph_auth_service_required` | string | `cephx`, `none` | service 인증 요구값 |
| `ceph_auth_client_required` | string | `cephx`, `none` | client 인증 요구값 |
| `ceph_clients` | list | client 정의 목록 | 서비스별 Ceph client |
| `ceph_deploy_keyrings` | boolean | `true`, `false` | keyring 배포 여부 |
| `ceph_auth_report_only` | boolean | `true`, `false` | 점검만 수행 여부 |

---

### 기본값 예시

```yaml
enable_cephx_enforcement: false

ceph_auth_cluster_required: cephx
ceph_auth_service_required: cephx
ceph_auth_client_required: cephx

ceph_deploy_keyrings: false
ceph_auth_report_only: true

ceph_clients:
  - name: client.glance
    keyring: /etc/ceph/ceph.client.glance.keyring
    caps:
      mon: "profile rbd"
      osd: "profile rbd pool=images"
```

---

### 정책값 변경 방법

1. CephX 상태 점검만 하려면 `ceph_auth_report_only: true`를 유지한다.
2. 실제 적용하려면 `enable_cephx_enforcement: true`로 설정한다.
3. 신규 OpenStack 서비스 client가 필요하면 `ceph_clients`에 추가한다.
4. keyring 배포까지 수행하려면 `ceph_deploy_keyrings: true`로 설정한다.
5. 운영 적용 전 Glance, Cinder, Nova 연동 테스트를 수행한다.

---

## 4.5 Ceph - root 이외 관리자 계정 사용

### 정책 판단

root 직접 사용은 감사 추적성을 약화시키므로 별도 관리자 계정과 sudo 기반 운영이 타당하다.

---

### 변경 가능한 정책값

| 변수명 | 타입 | 허용값 예시 | 설명 |
|---|---|---|---|
| `enable_ceph_admin_user_policy` | boolean | `true`, `false` | 관리자 계정 정책 활성화 여부 |
| `ceph_admin_users` | list | 사용자 목록 | Ceph 관리자 계정 |
| `ceph_admin_groups` | list | 그룹 목록 | 관리자 그룹 |
| `ceph_admin_sudo_nopasswd` | boolean | `true`, `false` | passwordless sudo 허용 여부 |
| `ceph_admin_sudo_commands` | list | 명령 목록 | 허용 sudo 명령 |
| `ceph_disable_root_ssh` | boolean | `true`, `false` | root SSH 차단 연계 여부 |

---

### 기본값 예시

```yaml
enable_ceph_admin_user_policy: true

ceph_admin_users:
  - cephadmin
  - ansible

ceph_admin_groups:
  - sudo

ceph_admin_sudo_nopasswd: true
ceph_admin_sudo_commands:
  - ALL

ceph_disable_root_ssh: true
```

---

### 정책값 변경 방법

1. 관리자 계정을 추가하려면 `ceph_admin_users`에 추가한다.
2. 관리자 그룹을 변경하려면 `ceph_admin_groups`를 수정한다.
3. passwordless sudo를 금지하려면 `ceph_admin_sudo_nopasswd: false`로 설정한다.
4. sudo 허용 명령을 제한하려면 `ceph_admin_sudo_commands`를 구체 명령 목록으로 변경한다.
5. root SSH 차단과 연계하지 않으려면 `ceph_disable_root_ssh: false`로 설정한다.
6. sudoers 변경 후 반드시 `visudo -cf`로 검증한다.

---

## 4.6 Ceph - SELinux 활성화

### 정책 판단

SELinux는 보안상 유효하지만 OpenStack, Kolla, Ceph 서비스와 충돌할 수 있으므로 단계 적용해야 한다.

---

### 변경 가능한 정책값

| 변수명 | 타입 | 허용값 예시 | 설명 |
|---|---|---|---|
| `enable_ceph_selinux` | boolean | `true`, `false` | SELinux 정책 적용 여부 |
| `ceph_selinux_state` | string | `disabled`, `permissive`, `enforcing` | SELinux 상태 |
| `ceph_selinux_policy` | string | `targeted` | SELinux policy |
| `ceph_selinux_install_packages` | boolean | `true`, `false` | 관련 패키지 설치 여부 |
| `ceph_selinux_allow_reboot` | boolean | `true`, `false` | 재부팅 허용 여부 |
| `ceph_selinux_report_avc` | boolean | `true`, `false` | AVC 로그 수집 여부 |

---

### 기본값 예시

```yaml
enable_ceph_selinux: false

ceph_selinux_state: permissive
ceph_selinux_policy: targeted

ceph_selinux_install_packages: true
ceph_selinux_allow_reboot: false
ceph_selinux_report_avc: true
```

---

### 정책값 변경 방법

1. SELinux 상태 점검만 하려면 `enable_ceph_selinux: false`를 유지한다.
2. 테스트 적용은 `ceph_selinux_state: permissive`로 시작한다.
3. 운영 강제 적용은 충분한 검증 후 `ceph_selinux_state: enforcing`으로 변경한다.
4. 재부팅이 필요한 환경이면 `ceph_selinux_allow_reboot: true`로 설정한다.
5. Enforcing 전환 전 `ausearch -m avc` 결과를 검토한다.

---

## 4.7 Ceph - 최신 보안 패치 적용

### 정책 판단

Ceph 보안 패치는 필요하지만 분산 스토리지 특성상 rolling 방식과 health check가 필요하다.

---

### 변경 가능한 정책값

| 변수명 | 타입 | 허용값 예시 | 설명 |
|---|---|---|---|
| `enable_ceph_patch` | boolean | `true`, `false` | Ceph 패치 활성화 여부 |
| `ceph_patch_mode` | string | `report`, `security_only`, `point_release`, `specific_version` | 패치 방식 |
| `ceph_target_version` | string | `19.2.3` | 목표 Ceph 버전 |
| `ceph_patch_health_required` | string | `HEALTH_OK`, `HEALTH_WARN` | 패치 전 요구 health 상태 |
| `ceph_rolling_patch` | boolean | `true`, `false` | rolling 방식 적용 여부 |
| `ceph_allow_reboot` | boolean | `true`, `false` | 재부팅 허용 여부 |
| `ceph_patch_batch_size` | integer | `1` | 한 번에 패치할 노드 수 |

---

### 기본값 예시

```yaml
enable_ceph_patch: false

ceph_patch_mode: report
ceph_target_version: ""

ceph_patch_health_required: HEALTH_OK
ceph_rolling_patch: true
ceph_allow_reboot: false
ceph_patch_batch_size: 1
```

---

### 정책값 변경 방법

1. 현재 상태 점검만 하려면 `ceph_patch_mode: report`로 설정한다.
2. 보안 패치만 수행하려면 `ceph_patch_mode: security_only`로 설정한다.
3. point release 업그레이드는 `ceph_patch_mode: point_release`로 설정한다.
4. 목표 버전을 지정하려면 `ceph_target_version`을 설정한다.
5. health 상태가 정상일 때만 적용하려면 `ceph_patch_health_required: HEALTH_OK`를 유지한다.
6. rolling 적용을 위해 `ceph_rolling_patch: true`를 유지한다.
7. 운영 노드는 `ceph_patch_batch_size: 1`로 순차 적용한다.

---

# 5. Storage 보안정책

---

## 5.1 Storage - root 계정 원격 접속 제한

### 정책 판단

root 원격 접속 제한은 권한 오남용과 감사 추적성 문제를 줄이기 위해 타당하다.

---

### 변경 가능한 정책값

| 변수명 | 타입 | 허용값 예시 | 설명 |
|---|---|---|---|
| `enable_storage_root_ssh_restrict` | boolean | `true`, `false` | root SSH 제한 여부 |
| `storage_permit_root_login` | string | `no`, `prohibit-password`, `yes` | PermitRootLogin 값 |
| `storage_password_authentication` | string | `yes`, `no` | PasswordAuthentication 값 |
| `storage_pubkey_authentication` | string | `yes`, `no` | PubkeyAuthentication 값 |
| `storage_sshd_config_path` | string | `/etc/ssh/sshd_config` | sshd 설정 파일 |
| `storage_sshd_dropin_path` | string | `/etc/ssh/sshd_config.d/99-storage-security.conf` | drop-in 설정 파일 |

---

### 기본값 예시

```yaml
enable_storage_root_ssh_restrict: true

storage_permit_root_login: "no"
storage_password_authentication: "no"
storage_pubkey_authentication: "yes"

storage_sshd_config_path: /etc/ssh/sshd_config
storage_sshd_dropin_path: /etc/ssh/sshd_config.d/99-storage-security.conf
```

---

### 정책값 변경 방법

1. root 접속을 완전히 차단하려면 `storage_permit_root_login: "no"`로 설정한다.
2. SSH key 기반 root 접속만 허용하려면 `storage_permit_root_login: "prohibit-password"`로 설정한다.
3. 패스워드 로그인을 차단하려면 `storage_password_authentication: "no"`로 설정한다.
4. 공개키 인증을 허용하려면 `storage_pubkey_authentication: "yes"`로 설정한다.
5. 변경 후 반드시 SSH 문법 검사를 수행한다.

   ```bash
   sshd -t
   ```

6. 관리자 계정 접속 가능 여부를 확인한 뒤 운영 적용한다.

---

## 5.2 Storage - 패스워드 복잡도 설정

### 정책 판단

패스워드 복잡도 설정은 무차별 대입 및 사전 공격 방어를 위해 타당하다.

---

### 변경 가능한 정책값

| 변수명 | 타입 | 허용값 예시 | 설명 |
|---|---|---|---|
| `enable_storage_password_complexity` | boolean | `true`, `false` | 패스워드 복잡도 정책 활성화 여부 |
| `password_minlen` | integer | `12`, `14` | 최소 길이 |
| `password_dcredit` | integer | `-1`, `0` | 숫자 요구 기준 |
| `password_ucredit` | integer | `-1`, `0` | 대문자 요구 기준 |
| `password_lcredit` | integer | `-1`, `0` | 소문자 요구 기준 |
| `password_ocredit` | integer | `-1`, `0` | 특수문자 요구 기준 |
| `password_retry` | integer | `3`, `5` | 재시도 횟수 |
| `password_dictcheck` | boolean | `true`, `false` | 사전 단어 검사 여부 |

---

### 기본값 예시

```yaml
enable_storage_password_complexity: true

password_minlen: 12
password_dcredit: -1
password_ucredit: -1
password_lcredit: -1
password_ocredit: -1
password_retry: 3
password_dictcheck: true
```

---

### 정책값 변경 방법

1. 최소 길이를 강화하려면 `password_minlen` 값을 증가시킨다.
2. 숫자를 필수로 요구하려면 `password_dcredit: -1`로 설정한다.
3. 숫자 필수 조건을 제거하려면 `password_dcredit: 0`으로 설정한다.
4. 대문자 필수 조건은 `password_ucredit`으로 제어한다.
5. 소문자 필수 조건은 `password_lcredit`으로 제어한다.
6. 특수문자 필수 조건은 `password_ocredit`으로 제어한다.
7. 재시도 횟수를 바꾸려면 `password_retry`를 수정한다.
8. 변경 후 약한 패스워드와 강한 패스워드 테스트를 모두 수행한다.

---

## 5.3 Storage - 계정 잠금 임계값 설정

### 정책 판단

로그인 실패 제한이 없으면 무차별 대입 공격이 가능하므로 계정 잠금 정책은 타당하다.

---

### 변경 가능한 정책값

| 변수명 | 타입 | 허용값 예시 | 설명 |
|---|---|---|---|
| `enable_storage_account_lock` | boolean | `true`, `false` | 계정 잠금 정책 활성화 여부 |
| `faillock_deny` | integer | `5`, `10` | 잠금 기준 실패 횟수 |
| `faillock_fail_interval` | integer | `900` | 실패 횟수 계산 시간 |
| `faillock_unlock_time` | integer | `600` | 자동 잠금 해제 시간 |
| `faillock_even_deny_root` | boolean | `true`, `false` | root 계정에도 적용 여부 |
| `faillock_admin_group_exempt` | boolean | `true`, `false` | 관리자 그룹 예외 여부 |

---

### 기본값 예시

```yaml
enable_storage_account_lock: true

faillock_deny: 5
faillock_fail_interval: 900
faillock_unlock_time: 600

faillock_even_deny_root: false
faillock_admin_group_exempt: false
```

---

### 정책값 변경 방법

1. 더 엄격하게 적용하려면 `faillock_deny` 값을 낮춘다.
2. 완화하려면 `faillock_deny` 값을 높인다.
3. 실패 횟수 계산 구간을 변경하려면 `faillock_fail_interval`을 수정한다.
4. 자동 해제 시간을 변경하려면 `faillock_unlock_time`을 수정한다.
5. root 계정에도 적용하려면 `faillock_even_deny_root: true`로 설정한다.
6. 관리자 잠금 사고를 줄이려면 `faillock_admin_group_exempt: true`를 검토한다.
7. 적용 후 실패 로그인 테스트를 수행한다.

---

## 5.4 Storage - 패스워드 최대 사용 기간 설정

### 정책 판단

패스워드 최대 사용 기간 제한은 타당하나, 서비스 계정과 자동화 계정은 예외 처리해야 한다.

---

### 변경 가능한 정책값

| 변수명 | 타입 | 허용값 예시 | 설명 |
|---|---|---|---|
| `enable_storage_password_age` | boolean | `true`, `false` | 패스워드 만료 정책 활성화 여부 |
| `password_max_days` | integer | `90`, `180` | 패스워드 최대 사용일 |
| `password_min_days` | integer | `1`, `7` | 패스워드 최소 사용일 |
| `password_warn_age` | integer | `7`, `14` | 만료 전 경고일 |
| `password_age_target_users` | list | 사용자 목록 | 적용 대상 사용자 |
| `password_age_excluded_users` | list | 사용자 목록 | 제외 대상 사용자 |
| `password_age_apply_existing_users` | boolean | `true`, `false` | 기존 계정에도 적용 여부 |

---

### 기본값 예시

```yaml
enable_storage_password_age: false

password_max_days: 90
password_min_days: 1
password_warn_age: 7

password_age_target_users:
  - admin
  - ansible

password_age_excluded_users:
  - root
  - ceph
  - nova
  - cinder
  - glance

password_age_apply_existing_users: false
```

---

### 정책값 변경 방법

1. 만료 주기를 늘리려면 `password_max_days` 값을 증가시킨다.
2. 더 엄격하게 하려면 `password_max_days` 값을 줄인다.
3. 만료 전 경고 기간을 변경하려면 `password_warn_age`를 수정한다.
4. 적용 대상 사용자는 `password_age_target_users`에 추가한다.
5. 서비스 계정은 `password_age_excluded_users`에 추가한다.
6. 기존 계정에도 적용하려면 `password_age_apply_existing_users: true`로 설정한다.
7. 적용 후 사용자별 정책을 확인한다.

   ```bash
   chage -l <username>
   ```

---

## 5.5 Storage - 불필요한 계정 제거

### 정책 판단

사용하지 않는 계정은 인증정보 악용 위험이 있으므로 비활성화 또는 삭제가 타당하다.

---

### 변경 가능한 정책값

| 변수명 | 타입 | 허용값 예시 | 설명 |
|---|---|---|---|
| `enable_storage_account_hardening` | boolean | `true`, `false` | Storage 계정 정리 정책 활성화 여부 |
| `storage_allowed_users` | list | 사용자 목록 | 유지할 계정 목록 |
| `storage_retired_users` | list | 사용자 목록 | 비활성화 또는 삭제 대상 계정 |
| `storage_account_action` | string | `report`, `lock`, `delete` | 처리 방식 |
| `storage_nologin_shell` | string | `/usr/sbin/nologin` | 잠금 시 적용할 shell |
| `storage_remove_home` | boolean | `true`, `false` | 홈 디렉터리 삭제 여부 |
| `storage_account_excluded_users` | list | 사용자 목록 | 제외 계정 목록 |

---

### 기본값 예시

```yaml
enable_storage_account_hardening: true

storage_allowed_users:
  - root
  - ansible
  - admin
  - ceph

storage_retired_users: []

storage_account_action: report
storage_nologin_shell: /usr/sbin/nologin
storage_remove_home: false

storage_account_excluded_users:
  - ansible
  - ceph
```

---

### 정책값 변경 방법

1. 유지 계정이 추가되면 `storage_allowed_users`에 추가한다.
2. 비활성화 대상 계정은 `storage_retired_users`에 추가한다.
3. 점검만 수행하려면 `storage_account_action: report`로 설정한다.
4. 계정 잠금을 수행하려면 `storage_account_action: lock`으로 설정한다.
5. 삭제까지 수행하려면 `storage_account_action: delete`로 설정한다.
6. 홈 디렉터리 삭제가 필요하면 `storage_remove_home: true`로 설정한다.
7. 운영 적용 전 check mode로 확인한다.

---

# 6. 코딩 에이전트 구현 요구사항

## 6.1 필수 구현 방식

코딩 에이전트는 다음 방식으로 Role을 구현한다.

1. 보안정책별 task 파일을 분리한다.
2. 각 task는 enable flag가 `true`일 때만 실행한다.
3. 위험 작업은 action mode가 `enforce` 또는 `delete`일 때만 수행한다.
4. 모든 정책값은 `defaults/main.yml`에 기본값을 둔다.
5. 운영 환경 값은 `group_vars` 또는 `host_vars`에서 재정의한다.
6. 설정 변경 전후 결과를 register로 저장한다.
7. SSH, sudoers, PAM 변경은 문법 검증 후 반영한다.
8. 삭제성 작업은 기본값을 비활성화한다.
9. 패치, SELinux, 방화벽 변경은 테스트 노드 우선 적용을 전제로 한다.

---

## 6.2 필수 tag 목록

```yaml
kvm_accounts
kvm_session_timeout
kvm_ip_restrict
kvm_default_bridge
kvm_log_backup
kvm_patch

ceph_keyring
ceph_ssh_keys
ceph_config
ceph_auth
ceph_admin_user
ceph_selinux
ceph_patch

storage_root_ssh
storage_password_complexity
storage_account_lock
storage_password_age
storage_accounts
```

---

## 6.3 정책 변경 후 공통 검증 명령

```bash
ansible-playbook -i inventories/prod/hosts.ini site.yml --syntax-check
```

```bash
ansible-playbook -i inventories/prod/hosts.ini site.yml --check --diff
```

```bash
ansible-playbook -i inventories/prod/hosts.ini site.yml \
  --tags <tag_name> \
  --limit test_hosts \
  --check --diff
```

```bash
ansible-playbook -i inventories/prod/hosts.ini site.yml \
  --tags <tag_name> \
  --limit test_hosts
```

---

# 7. 정책 변경 예시

## 7.1 SSH Timeout 완화

```yaml
ssh_client_alive_interval: 600
ssh_client_alive_count_max: 2
shell_timeout: 600
```

적용:

```bash
ansible-playbook -i inventories/prod/hosts.ini site.yml \
  --tags kvm_session_timeout \
  --check --diff
```

---

## 7.2 관리자 IP 대역 추가

```yaml
allowed_management_cidrs:
  - 10.0.0.0/24
  - 192.168.10.0/24
  - 10.20.30.0/24
```

적용:

```bash
ansible-playbook -i inventories/prod/hosts.ini site.yml \
  --tags kvm_ip_restrict \
  --limit test_hosts
```

---

## 7.3 패스워드 복잡도 강화

```yaml
password_minlen: 14
password_dcredit: -1
password_ucredit: -1
password_lcredit: -1
password_ocredit: -1
```

적용:

```bash
ansible-playbook -i inventories/prod/hosts.ini site.yml \
  --tags storage_password_complexity \
  --check --diff
```

---

## 7.4 Ceph keyring 권한 강화

```yaml
ceph_keyring_policy:
  - path: /etc/ceph/ceph.client.admin.keyring
    owner: root
    group: root
    mode: "0600"
```

적용:

```bash
ansible-playbook -i inventories/prod/hosts.ini site.yml \
  --tags ceph_keyring \
  --limit ceph_hosts
```

---

# 8. README.md 작성 요구사항

코딩 에이전트는 Role의 `README.md`에 다음 내용을 포함해야 한다.

1. Role 목적
2. 적용 대상 노드 그룹
3. 지원 OS
4. 전체 변수 목록
5. 정책별 변수 설명
6. 변수 기본값
7. 정책값 변경 방법
8. `group_vars` 예시
9. `host_vars` 예시
10. `extra-vars` 적용 예시
11. check mode 실행 방법
12. tag별 실행 방법
13. 항목별 검증 명령
14. 위험 조치 enable flag 목록
15. rollback 또는 비활성화 방법
16. 증적 산출 방식

---

# 9. 구현 시 주의사항

1. 정책값 변경은 task 수정이 아니라 변수 수정으로 처리한다.
2. 위험도가 높은 조치는 기본값을 `false` 또는 `report`로 둔다.
3. 삭제성 작업은 별도 action 값이 `delete`일 때만 실행한다.
4. SSH 설정 변경 후 반드시 `sshd -t`를 수행한다.
5. sudoers 변경 후 반드시 `visudo -cf`를 수행한다.
6. PAM 변경은 배포판별 구조를 확인한 뒤 적용한다.
7. IP 접근 제한은 반드시 테스트 노드에서 먼저 적용한다.
8. CephX, SELinux, 패치는 별도 PoC 후 운영 반영한다.
9. 모든 조치 결과는 register로 저장해 증적화할 수 있어야 한다.
10. 운영 예외는 `host_vars`로 관리한다.
11. 정책 변경 이력은 Git commit 또는 변경관리 문서로 남긴다.