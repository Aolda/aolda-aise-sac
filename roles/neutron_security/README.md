# neutron_security

OpenStack Neutron API 인증서 및 TLS 조정 항목을 추후 적용 가능하게 scaffold화한 Ansible Role입니다.

## 적용 대상

- `openstack_nodes`

## 목적

- Neutron API 인증서 조정 항목을 추후 적용 가능하게 scaffold 구조로 준비합니다.
- Neutron TLS 조정 항목을 추후 적용 가능하게 scaffold 구조로 준비합니다.
- 실제 OpenStack/Kolla/Neutron 설정을 지금 바로 변경하지 않고 변수 기반 분기만 제공합니다.

## 기본 동작

- 기본값은 모두 `false` 또는 빈 문자열이므로 현재는 실제 설정 변경이 실행되지 않습니다.
- 기본 실행 모드인 `audit`에서는 debug 메시지만 출력합니다.
- `harden` 모드에서도 enabled와 confirmed 조건, 경로 변수, 서비스명이 모두 충족되지 않으면 실제 task는 실행되지 않습니다.

## 변수 설명

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `network_security_mode` | `audit` | 실행 모드입니다. `audit`에서는 debug만 수행하고 `harden`에서만 scaffold task가 실행 가능합니다. |
| `neutron_security_api_cert_enabled` | `false` | Neutron API 인증서 scaffold 실행 여부입니다. |
| `neutron_security_api_cert_confirmed` | `false` | Neutron API 인증서 scaffold 재확인 플래그입니다. |
| `neutron_security_tls_enabled` | `false` | Neutron TLS scaffold 실행 여부입니다. |
| `neutron_security_tls_confirmed` | `false` | Neutron TLS scaffold 재확인 플래그입니다. |
| `neutron_security_config_path` | `""` | Neutron 설정 파일 경로입니다. |
| `neutron_security_cert_file` | `""` | 인증서 파일 경로입니다. |
| `neutron_security_key_file` | `""` | 개인키 파일 경로입니다. |
| `neutron_security_ca_file` | `""` | CA 파일 경로입니다. |
| `neutron_security_service_name` | `""` | 재시작 대상 Neutron 서비스명입니다. |

## 주의사항

- 실제 OpenStack/Kolla/Neutron 설정 경로를 먼저 확인한 뒤에만 `harden` 모드를 검토해야 합니다.
- 인증서/TLS scaffold는 enabled와 confirmed가 모두 `true`여도 경로 변수와 서비스명이 비어 있으면 실행되지 않습니다.
- 실제 운영 반영 전에는 테스트베드에서만 먼저 검증해야 합니다.
