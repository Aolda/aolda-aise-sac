# os_firewall

Linux 기반 OpenStack/Ceph 노드의 `iptables` 상태를 점검하고, ICMP rate limit 및 fragment packet drop 설정을 적용하는 Ansible Role입니다.

## 구현 task

| 파일 | 구현 내용 |
| --- | --- |
| `tasks/main.yml` | `audit` 모드에서 현재 `iptables` 규칙을 조회하고, `harden` 모드에서 ICMP `echo-request` rate limit 규칙과 fragment packet drop 규칙을 적용합니다. allowlist, 기본 `DROP`, 차단 로그는 기본 비활성화된 scaffold로만 제공합니다. |

## 적용이 필요한 이유

- 현재 방화벽 규칙 상태를 먼저 점검해야 운영 환경에 미치는 영향을 예측할 수 있습니다.
- ICMP `echo-request` rate limit은 과도한 ping 요청에 대한 기본적인 제어 수단이 됩니다.
- fragment packet drop은 비정상적이거나 우회성 있는 패킷 처리 위험을 줄이는 데 도움이 됩니다.
- 전체 `DROP` 정책이나 포트 allowlist는 서비스 영향도가 크므로 기본 비활성화 상태에서 변수 기반으로만 준비해 두는 편이 안전합니다.

## 적용 시 변경점

- `audit` 모드에서는 `iptables -S` 결과를 조회만 하고 실제 규칙은 변경하지 않습니다.
- `harden` 모드에서는 ICMP `echo-request` 허용 속도 및 burst 기준에 따라 관련 규칙이 추가됩니다.
- `harden` 모드에서는 fragment packet drop 규칙이 추가됩니다.
- allowlist, 기본 `DROP`, 차단 로그는 enabled 변수 값을 명시적으로 켠 경우에만 scaffold task가 실행됩니다.

## 변수 설명

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `network_security_mode` | `audit` | 실행 모드입니다. `audit`에서는 조회만 수행하고 `harden`에서만 규칙을 적용합니다. |
| `os_firewall_icmp_echo_request_limit` | `5/second` | ICMP `echo-request` 허용 속도 제한값입니다. |
| `os_firewall_icmp_echo_request_burst` | `10` | ICMP `echo-request` burst 허용치입니다. |
| `os_firewall_apply_fragment_drop` | `true` | fragment packet drop 규칙 적용 여부입니다. |
| `os_firewall_allowlist_enabled` | `false` | allowlist scaffold 실행 여부입니다. |
| `os_firewall_default_drop_enabled` | `false` | 기본 `DROP` scaffold 실행 여부입니다. |
| `os_firewall_drop_logging_enabled` | `false` | 차단 로그 scaffold 실행 여부입니다. |
| `os_firewall_allowed_tcp_ports` | `[]` | allowlist 대상 TCP 포트 목록입니다. |
| `os_firewall_allowed_udp_ports` | `[]` | allowlist 대상 UDP 포트 목록입니다. |
| `os_firewall_allowed_source_cidrs` | `[]` | allowlist 허용 소스 CIDR 목록입니다. |
| `os_firewall_drop_log_prefix` | `"AISE_DROP"` | 차단 로그 prefix 값입니다. |

## 기본 비활성화된 선택 기능

- `os_firewall_allowlist_enabled: false`일 때 Linux 필수 포트 allowlist scaffold는 실행되지 않습니다.
- `os_firewall_default_drop_enabled: false`일 때 전체 기본 정책 `DROP` scaffold는 실행되지 않습니다.
- `os_firewall_drop_logging_enabled: false`일 때 차단 로그 scaffold는 실행되지 않습니다.
- OpenStack/Ceph 필수 포트 허용 정책은 변수 값 확정 후 활성화가 필요합니다.

## 주의사항

- `harden` 모드는 `network_security_mode: harden`일 때만 적용됩니다.
- 현재 규칙은 `iptables` 기준이며, 배포 환경의 영속화 방식은 별도 검토가 필요합니다.
- 적용 전 운영 표준 포트와 서비스 의존성을 확정해야 합니다.
- 기본 비활성화된 선택 기능은 실제 운영 적용 전 테스트베드에서 먼저 검증해야 합니다.
