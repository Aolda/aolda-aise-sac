# network_hardening

MikroTik RouterOS 기반 네트워크 장비의 service, user, SNMP, interface 상태를 점검하고 관리 접근 제한 및 사용자 세션 timeout 정책을 적용하는 Ansible Role입니다.

## 구현 task

| 파일 | 구현 내용 |
| --- | --- |
| `tasks/main.yml` | `audit` 모드에서 RouterOS service, user, SNMP, interface 상태를 조회하고, `harden` 모드에서 관리 접근 허용 CIDR 제한, 불필요한 관리 서비스 비활성화, 선택 사용자 대상 session timeout 적용, SNMP 비활성화 구조를 수행합니다. 미사용 포트 shutdown은 제외합니다. |

## 적용이 필요한 이유

- RouterOS 관리 서비스가 과도하게 열려 있으면 네트워크 장비의 관리면 공격 범위가 넓어질 수 있습니다.
- 허용된 관리망에서만 접근하도록 제한하면 장비 직접 접속 위험을 줄일 수 있습니다.
- 사용하지 않는 관리 서비스는 비활성화하는 편이 보안상 유리합니다.
- 사용자별 session timeout은 장시간 방치된 관리 세션 악용 가능성을 줄이는 데 도움이 됩니다.
- SNMP는 필요 여부가 명확하지 않으면 우선 비활성화하는 편이 안전합니다.

## 적용 시 변경점

- `audit` 모드에서는 RouterOS service, user, SNMP, interface 상태를 조회만 하고 실제 설정은 변경하지 않습니다.
- `harden` 모드에서는 `network_hardening_allowed_management_cidrs` 값으로 SSH 및 Winbox 관리 접근 주소가 제한됩니다.
- `network_hardening_disabled_services` 목록에 포함된 관리 서비스가 비활성화됩니다.
- `network_hardening_session_timeout_users`가 지정된 경우에만 해당 사용자에 대해 inactivity timeout 및 inactivity policy가 적용됩니다.
- `network_hardening_disable_snmp`가 `true`이면 SNMP가 비활성화됩니다.
- 미사용 포트 shutdown은 적용하지 않습니다.

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
