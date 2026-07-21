# network_hardening

MikroTik RouterOS 기반 네트워크 장비의 service, user, SNMP, interface 상태를 점검하고 관리 접근 제한 및 사용자 세션 timeout 정책을 적용하는 Ansible Role입니다.

## 구현 task

| 파일 | 구현 내용 |
| --- | --- |
| `tasks/main.yml` | `audit` 모드에서 RouterOS service, user, SNMP, interface 상태를 조회하고, `harden` 모드에서 관리 접근 허용 CIDR 제한, 불필요한 관리 서비스 비활성화, 선택 사용자 대상 session timeout 적용, SNMP 비활성화 구조를 수행합니다. 미사용 인터페이스 disable, `rp-filter`, DoS protection, 기본 `drop`, logging은 기본 비활성화된 scaffold로만 제공합니다. |

## 적용이 필요한 이유

- RouterOS 관리 서비스가 과도하게 열려 있으면 네트워크 장비의 관리면 공격 범위가 넓어질 수 있습니다.
- 허용된 관리망에서만 접근하도록 제한하면 장비 직접 접속 위험을 줄일 수 있습니다.
- 사용하지 않는 관리 서비스는 비활성화하는 편이 보안상 유리합니다.
- 사용자별 session timeout은 장시간 방치된 관리 세션 악용 가능성을 줄이는 데 도움이 됩니다.
- 향후 확장 가능한 보류 정책은 기본 비활성화 상태에서 RouterOS command 기반 scaffold로만 준비해 두는 편이 안전합니다.

## 적용 시 변경점

- `audit` 모드에서는 RouterOS service, user, SNMP, interface 상태를 조회만 하고 실제 설정은 변경하지 않습니다.
- `harden` 모드에서는 `network_hardening_allowed_management_cidrs` 값으로 SSH 및 Winbox 관리 접근 주소가 제한됩니다.
- `network_hardening_disabled_services` 목록에 포함된 관리 서비스가 비활성화됩니다.
- `network_hardening_session_timeout_users`가 지정된 경우에만 해당 사용자에 대해 inactivity timeout 및 inactivity policy가 적용됩니다.
- `network_hardening_disable_snmp`가 `true`이면 SNMP가 비활성화됩니다.
- 미사용 인터페이스 disable, `rp-filter`, DoS protection, 기본 `drop`, logging은 enabled 변수 값을 명시적으로 켠 경우에만 scaffold task가 실행됩니다.

## 변수 설명

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `network_security_mode` | `audit` | 실행 모드입니다. `audit`에서는 조회만 수행하고 `harden`에서만 설정을 적용합니다. |
| `network_hardening_allowed_management_cidrs` | `[]` | 관리 접근을 허용할 CIDR 목록입니다. `harden` 모드에서는 값이 비어 있으면 실패합니다. |
| `network_hardening_disabled_services` | `["telnet", "ftp", "www", "www-ssl", "api", "api-ssl"]` | 비활성화할 RouterOS 관리 서비스 목록입니다. |
| `network_hardening_ssh_service_name` | `ssh` | 관리 접근 제한 대상 SSH 서비스명입니다. |
| `network_hardening_winbox_service_name` | `winbox` | 관리 접근 제한 대상 Winbox 서비스명입니다. |
| `network_hardening_session_timeout_users` | `[]` | session timeout을 적용할 RouterOS 사용자 목록입니다. 비어 있으면 관련 task는 실행되지 않습니다. |
| `network_hardening_session_timeout` | `10m` | 사용자 inactivity timeout 값입니다. |
| `network_hardening_session_inactivity_policy` | `logout` | inactivity 발생 시 적용할 정책입니다. |
| `network_hardening_disable_snmp` | `true` | SNMP 비활성화 여부입니다. |
| `network_hardening_unused_port_shutdown_enabled` | `false` | 미사용 인터페이스 disable scaffold 실행 여부입니다. |
| `network_hardening_unused_interfaces` | `[]` | disable 대상 인터페이스 목록입니다. |
| `network_hardening_rp_filter_enabled` | `false` | RouterOS `rp-filter` scaffold 실행 여부입니다. |
| `network_hardening_rp_filter_mode` | `"loose"` | RouterOS `rp-filter` 값입니다. |
| `network_hardening_dos_protection_enabled` | `false` | DoS protection scaffold 실행 여부입니다. |
| `network_hardening_dos_rules` | `[]` | RouterOS command 기반 DoS protection rule 목록입니다. |
| `network_hardening_default_drop_enabled` | `false` | 기본 `drop` scaffold 실행 여부입니다. |
| `network_hardening_drop_logging_enabled` | `false` | logging scaffold 실행 여부입니다. |

## 기본 비활성화된 선택 기능

- `network_hardening_unused_port_shutdown_enabled: false`일 때 미사용 인터페이스 disable scaffold는 실행되지 않습니다.
- `network_hardening_rp_filter_enabled: false`일 때 RouterOS `rp-filter` scaffold는 실행되지 않습니다.
- `network_hardening_dos_protection_enabled: false`일 때 DoS protection scaffold는 실행되지 않습니다.
- `network_hardening_default_drop_enabled: false`일 때 기본 `drop` scaffold는 실행되지 않습니다.
- `network_hardening_drop_logging_enabled: false`일 때 logging scaffold는 실행되지 않습니다.
- 장비별 허용 관리망 CIDR, DoS rule, unused interface 목록은 변수 값 확정 후 활성화가 필요합니다.

## 주의사항

- `harden` 모드는 `network_security_mode: harden`일 때만 적용됩니다.
- 관리망 CIDR을 지정하지 않으면 harden 단계는 실패하도록 구성되어 있습니다.
- RouterOS 명령은 `community.routeros` collection과 `ansible.netcommon` 연결 설정을 전제로 합니다.
- 실제 장비 접속 정보와 주소는 인벤토리 또는 안전한 변수 저장소에서 별도 관리해야 합니다.
- 기본 비활성화된 선택 기능은 실제 운영 적용 전 테스트베드에서 먼저 검증해야 합니다.
