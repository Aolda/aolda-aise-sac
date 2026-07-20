# cinder-security

KISA 클라우드 취약점 가이드의 OpenStack Cinder 항목을 적용합니다.

- `auth_strategy = keystone`
- Keystone/Nova/Glance TLS 통신
- `max_request_body_size` 설정

설정파일 소유권/권한 hardening과 Barbican/KMS 기반 암호화 볼륨 타입 설정은 원본 OpenStack 인증/인가 16개 밖의 확장 항목이므로 기본 실행에서 제외합니다. TLS는 `cinder_security_enable_tls`, 볼륨 암호화 확장은 `cinder_security_include_volume_encryption_extension`과 `cinder_security_enable_volume_encryption`으로 제어합니다. 서비스 재시작은 기본 자동 실행하지 않습니다.
