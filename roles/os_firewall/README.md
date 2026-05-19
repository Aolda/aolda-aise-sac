# os_firewall

Linux 기반 OpenStack/Ceph 노드의 `iptables` 상태를 점검하고, ICMP rate limit 및 fragment packet drop 설정을 적용하는 Ansible Role입니다.

## 구현 task

| 파일 | 구현 내용 |
| --- | --- |
| `tasks/main.yml` | `audit` 모드에서 현재 `iptables` 규칙을 조회하고, `harden` 모드에서 ICMP `echo-request` rate limit 규칙과 fragment packet drop 규칙을 적용합니다. 전체 기본 정책 `DROP`, 차단 로그, 필수 포트 allowlist 적용은 제외합니다. |

## 적용이 필요한 이유

- 현재 방화벽 규칙 상태를 먼저 점검해야 운영 환경에 미치는 영향을 예측할 수 있습니다.
- ICMP `echo-request` rate limit은 과도한 ping 요청에 대한 기본적인 제어 수단이 됩니다.
- fragment packet drop은 비정상적이거나 우회성 있는 패킷 처리 위험을 줄이는 데 도움이 됩니다.
- 전체 `DROP` 정책이나 포트 allowlist는 서비스 영향도가 크므로 초기 단계에서는 보수적으로 제외하는 편이 안전합니다.

## 적용 시 변경점

- `audit` 모드에서는 `iptables -S` 결과를 조회만 하고 실제 규칙은 변경하지 않습니다.
- `harden` 모드에서는 ICMP `echo-request` 허용 속도 및 burst 기준에 따라 관련 규칙이 추가됩니다.
- `harden` 모드에서는 fragment packet drop 규칙이 추가됩니다.
- 전체 기본 정책을 `DROP`으로 바꾸지 않으며, 차단 로그 정책과 필수 포트 allowlist도 적용하지 않습니다.

## 변수 설명

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `network_security_mode` | `audit` | 실행 모드입니다. `audit`에서는 조회만 수행하고 `harden`에서만 규칙을 적용합니다. |
| `os_firewall_icmp_echo_request_limit` | `5/second` | ICMP `echo-request` 허용 속도 제한값입니다. |
| `os_firewall_icmp_echo_request_burst` | `10` | ICMP `echo-request` burst 허용치입니다. |
| `os_firewall_apply_fragment_drop` | `true` | fragment packet drop 규칙 적용 여부입니다. |
