# neutron-security

KISA 클라우드 취약점 가이드의 OpenStack Neutron 항목을 적용합니다.

- 네트워킹 서비스 설정파일 소유권/권한
- `auth_strategy = keystone`
- Keystone 인증 HTTPS 통신
- Neutron API 서버 TLS 활성화

TLS/HTTPS 설정은 `neutron_security_enable_tls: true`일 때만 적용합니다.
