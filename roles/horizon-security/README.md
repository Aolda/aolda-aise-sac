# horizon-security

KISA 클라우드 취약점 가이드의 OpenStack ACC/Horizon 항목을 적용합니다.

- `CSRF_COOKIE_SECURE`
- `SESSION_COOKIE_SECURE`
- `SESSION_COOKIE_HTTPONLY`
- `AUTH_PASSWORD_VALIDATORS`

Secure Cookie 설정은 `horizon_security_enable_secure_cookie: true`일 때만 적용하며, HTTPS endpoint 검증을 먼저 수행합니다.
