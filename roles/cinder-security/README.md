# cinder-security

KISA 클라우드 취약점 가이드의 OpenStack Cinder 항목을 적용합니다.

- 블록스토리지 설정파일 소유권/권한
- `auth_strategy = keystone`
- Keystone/Nova/Glance TLS 통신
- `max_request_body_size` 설정
- Barbican/KMS 확인 후 암호화 볼륨 타입 설정

TLS는 `cinder_security_enable_tls`, 볼륨 암호화는 `cinder_security_enable_volume_encryption`으로 제어합니다. 서비스 재시작은 기본 자동 실행하지 않습니다.
