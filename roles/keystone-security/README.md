# keystone-security

KISA 클라우드 취약점 가이드의 OpenStack Keystone 항목을 적용합니다.

- Identity 설정파일 소유권/권한
- Identity TLS 활성화
- PKI 토큰 해시 알고리즘 강화
- `max_request_body_size` 설정
- `admin_token` 제거

TLS는 `keystone_security_enable_tls: true`일 때만 적용하며, HTTPS endpoint와 인증서 파일을 먼저 검증합니다. 서비스 재시작은 기본 비활성화이며 `keystone_security_restart_service: true`로 제어합니다.
