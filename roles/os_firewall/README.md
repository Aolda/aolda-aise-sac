# os_firewall

## 적용 대상
- Linux 기반 OpenStack 노드
- Ceph 관련 Linux 노드

## 구현 항목
- `audit` 모드에서 현재 `iptables` 규칙 조회
- `harden` 모드에서 ICMP `echo-request` rate limit 규칙 적용
- `harden` 모드에서 fragment packet drop 규칙 적용
- 기본 실행 모드를 `audit`로 유지

## 제외/보류 항목
- 전체 기본 정책을 `DROP`으로 설정하는 작업 제외
- 차단 로그 정책 적용 제외
- Linux 필수 포트 allowlist 적용 제외
- OpenStack/Ceph 필수 포트 허용 정책은 후속 단계에서 확정 예정

## 변수 설명
- `network_security_mode`: `audit` 또는 `harden`
- `os_firewall_icmp_echo_request_limit`: ICMP `echo-request` 허용 속도
- `os_firewall_icmp_echo_request_burst`: ICMP `echo-request` burst 허용치
- `os_firewall_apply_fragment_drop`: fragment packet drop 적용 여부

## 실행 방법
```bash
ansible-galaxy collection install -r requirements.yml
ansible-playbook playbooks/network_security.yml --limit openstack_nodes
ansible-playbook playbooks/network_security.yml --limit openstack_nodes -e network_security_mode=harden
```

## 주의사항
- `harden` 모드는 `network_security_mode: harden`일 때만 적용된다.
- 현재 규칙은 `iptables` 기준이며, 배포 환경의 영속화 방식은 별도 검토가 필요하다.
- 적용 전 운영 표준 포트와 서비스 의존성을 확정해야 한다.
