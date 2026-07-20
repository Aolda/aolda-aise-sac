# nova-security

KISA 클라우드 취약점 가이드의 OpenStack Nova 항목을 적용합니다.

- Compute 설정파일 소유권/권한
- `auth_strategy = keystone`
- Keystone 인증 HTTPS 통신
- Nova와 Glance의 HTTPS 통신

TLS/HTTPS 설정은 `nova_security_enable_tls: true`일 때만 적용하며, endpoint 사전 검증 후 설정합니다. 서비스 재시작은 `nova_security_restart_service`로 제어합니다.
