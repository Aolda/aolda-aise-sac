# network_hardening

## 적용 대상
- MikroTik RouterOS 기반 라우터
- MikroTik RouterOS 기반 스위치

## 구현 항목
- `audit` 모드에서 RouterOS service 상태 조회
- `audit` 모드에서 RouterOS user 상태 조회
- `audit` 모드에서 RouterOS SNMP 상태 조회
- `audit` 모드에서 RouterOS interface 상태 조회
- `harden` 모드에서 관리 접근 제한 구조 작성
- `harden` 모드에서 선택한 사용자 대상 session timeout 적용 구조 작성
- `harden` 모드에서 SNMP disable 구조 작성

## 제외/보류 항목
- 미사용 포트 shutdown 제외
- Cisco IOS 모듈 사용 제외
- 장비별 허용 관리망 CIDR 확정 전 세부 정책 보류
- 서비스별 포트 수준 세분화 정책은 후속 단계에서 정리 예정

## 변수 설명
- `network_security_mode`: `audit` 또는 `harden`
- `network_hardening_allowed_management_cidrs`: 관리 접근 허용 CIDR 목록
- `network_hardening_disabled_services`: 비활성화할 RouterOS 관리 서비스 목록
- `network_hardening_ssh_service_name`: 접근 제한 대상 SSH 서비스명
- `network_hardening_winbox_service_name`: 접근 제한 대상 Winbox 서비스명
- `network_hardening_session_timeout_users`: session timeout 적용 대상 사용자 목록
- `network_hardening_session_timeout`: 사용자 inactivity timeout 값
- `network_hardening_session_inactivity_policy`: inactivity 발생 시 처리 정책
- `network_hardening_disable_snmp`: SNMP 비활성화 여부

## 실행 방법
```bash
ansible-galaxy collection install -r requirements.yml
ansible-playbook playbooks/network_security.yml --limit network_gear
ansible-playbook playbooks/network_security.yml --limit network_gear -e network_security_mode=harden
```

## 주의사항
- `harden` 모드는 `network_security_mode: harden`일 때만 적용된다.
- 관리망 CIDR을 지정하지 않으면 harden 단계는 실패하도록 구성되어 있다.
- RouterOS 명령은 `community.routeros` collection과 `ansible.netcommon` 연결 설정을 전제로 한다.
- 실제 장비 접속 정보와 주소는 인벤토리 또는 안전한 변수 저장소에서 별도 관리해야 한다.
