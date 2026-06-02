# Architecture

AISE는 Ansible role 단위로 인프라 컴포넌트 보안 설정과 점검을 분리합니다. 기본 원칙은 운영 영향이 큰 변경을 자동 적용하지 않고, 명시 변수로 활성화한 경우에만 적용하는 것입니다.

## Role Layout

| 영역 | Role | 실행 대상 | 기본 동작 |
| --- | --- | --- | --- |
| DB | `db-security` | MariaDB/MySQL 노드 | 계정/권한/로그/설정 파일 권한 관리 및 validate |
| Docker | `docker-security` | Docker 호스트 | 파일 권한과 런타임 check-only 중심 |
| Kubernetes | `k8s-security` | control-plane/worker 노드 | precheck, 역할별 조건 적용, check-only 중심 |
| OpenStack | `*-security` | 컴포넌트별 노드 | Keystone/Nova/Cinder/Glance/Neutron 인증/인가 16개 항목과 조건부 TLS/검증 |

## Execution Flow

모든 role은 가능한 한 아래 흐름을 따릅니다.

| 단계 | 목적 |
| --- | --- |
| Defaults | 위험 작업은 `defaults/main.yml`에서 `false`로 시작 |
| Precheck | 설정 파일, 인증서, endpoint, 노드 역할 등 선행 조건 확인 |
| Apply | 파일 권한, 설정값, check-only 항목을 role별 task에서 처리 |
| Handler | 서비스 재시작은 명시 변수와 handler로 분리 |
| Validate | 실제 파일 내용, 권한, 런타임 상태를 `assert` 또는 read-only command로 확인 |

운영 영향이 큰 변경은 구현되어 있어도 기본값이 비활성입니다. 대표적으로 패키지 업데이트, Docker daemon 재시작, Kubernetes static pod manifest 변경, OpenStack TLS 전환이 여기에 해당합니다. 원본 50개 밖의 Horizon, Cinder 볼륨 암호화, OpenStack 설정 파일 권한 hardening, Docker daemon 옵션 병합은 기본 실행에서 제외합니다.

## Component Safety Model

| 컴포넌트 | 자동 적용 중심 | 기본 비활성/수동 중심 |
| --- | --- | --- |
| DB | 계정 정리, 권한 제한, 로그/설정 파일 권한, slow/error log 설정 | `general_log`, 패키지 업데이트, 운영 계정 예외 검토 |
| Docker | systemd/socket/daemon 파일 권한, runtime 점검 | audit rule 적용, Content Trust 강제, SELinux/PIDs/no-new-privileges/컨테이너 SSH 자동 조치, daemon JSON 보안 옵션 병합 |
| Kubernetes | 노드 역할별 precheck, 백업, validate, check-only 정책 점검 | API server/etcd/kubelet 위험 변경, NetworkPolicy/PSA 강제 적용, Secret 재암호화 |
| OpenStack | Keystone/Nova/Cinder/Glance 인증 설정, max_request_body_size, admin_token 제거, validate | 전체 TLS 전환, Horizon Secure Cookie, Cinder volume encryption, conf 파일 권한 hardening, Neutron auth_strategy 추가 보강 |

## Kubernetes Role Structure

Kubernetes role은 실제 클러스터 노드 역할 차이를 반영해 아래 흐름으로 실행됩니다.

| 단계 | 파일 | 역할 |
| --- | --- | --- |
| Precheck | `roles/k8s-security/tasks/precheck.yml` | control-plane/worker 파일 존재 여부, static pod YAML 파싱, etcd TLS 인증서 존재, kubectl client version 확인 |
| Control Plane | `roles/k8s-security/tasks/1_control_plane.yml` | controller-manager 인자, control-plane 파일/인증서 권한 관리 |
| API Server | `roles/k8s-security/tasks/2_api_server.yml` | kube-apiserver 인증/인가/TLS/audit 설정. Admission Plugin은 기본 check-only |
| etcd | `roles/k8s-security/tasks/3_etcd.yml` | etcd TLS는 인증서가 모두 있을 때만 명시 변수로 적용. etcd encryption은 manual-required |
| Worker | `roles/k8s-security/tasks/4_kubelet.yml` | kubelet config가 있는 worker/control-plane 노드에서만 적용 |
| Common Policy | `roles/k8s-security/tasks/5_policies.yml` | PSA/NetworkPolicy check-only 조회. 실제 적용은 명시 변수 필요 |
| Pod Checks | `roles/k8s-security/tasks/6_pod_security_checks.yml` | 기존 Pod 보안 상태 점검 |
| Validate | `roles/k8s-security/tasks/validate.yml` | static pod YAML 재파싱, kube-apiserver/etcd/kubelet 설정 assert |

## Kubernetes Safety Defaults

운영 영향이 큰 Kubernetes 변경은 기본값이 `false`입니다.

| 변수 | 기본값 | 이유 |
| --- | --- | --- |
| `k8s_apply_control_plane` | `false` | control-plane static pod manifest 변경 방지 |
| `k8s_apply_api_server` | `false` | API server 재기동 위험 방지 |
| `k8s_apply_etcd_tls` | `false` | etcd 인증서/클러스터 구성 차이 반영 |
| `k8s_apply_etcd_encryption_config` | `false` | 기존 Secret 재암호화가 필요한 manual-required 절차 |
| `k8s_apply_kubelet` | `false` | worker workload 영향 방지 |
| `k8s_apply_policies` | `false` | PSA/NetworkPolicy로 인한 워크로드 차단 방지 |
| `k8s_apply_admission_plugins` | `false` | Kubernetes 버전별 plugin 호환성 차이 |
| `k8s_restart_kubelet` | `false` | kubelet 재시작에 따른 node 영향 방지 |

`k8s_check_policies`와 `k8s_enable_pod_security_checks`는 기본 check-only 용도로 사용합니다.

## etcd Encryption Manual Procedure

etcd Secret 암호화는 role이 완전 자동 적용하지 않습니다. 운영자는 별도 절차로 다음을 수행해야 합니다.

1. etcd snapshot과 control-plane manifest를 백업합니다.
2. `EncryptionConfiguration` 파일과 key를 준비합니다.
3. kube-apiserver에 `--encryption-provider-config`를 적용할 계획을 수립합니다.
4. API server 재기동 후 신규 Secret 암호화를 확인합니다.
5. 기존 Secret은 읽고 다시 적용하는 방식으로 재암호화합니다.
6. 장애 시 복구 절차를 검증한 뒤 운영 반영합니다.

이 role은 위 절차를 자동 실행하지 않으며, `k8s_acknowledge_secret_reencryption_required`와 관련 적용 변수를 명시한 경우에만 파일/인자 설정을 시도합니다.

## OpenStack TLS Safety

OpenStack TLS는 단일 설정값 변경이 아니라 인증서, CA trust, endpoint catalog, 로드밸런서, 클라이언트 환경을 함께 바꾸는 작업입니다. 따라서 role은 TLS 설정 task를 제공하되 기본 자동 적용하지 않습니다.

| Role | TLS 적용 선행 변수 |
| --- | --- |
| Keystone | `keystone_security_enable_tls`, `keystone_security_tls_endpoint_change_confirmed` |
| Nova | `nova_security_enable_tls`, `nova_security_keystone_tls_confirmed` |
| Cinder | `cinder_security_enable_tls`, `cinder_security_keystone_tls_confirmed` |
| Glance | `glance_security_enable_tls`, `glance_security_keystone_tls_confirmed` |
| Neutron | `neutron_security_enable_tls`, `neutron_security_keystone_tls_confirmed` |
| Horizon | 원본 50개 밖 확장 role로 기본 playbook에서 제외 |

각 role의 precheck는 설정 파일 존재, HTTPS endpoint 형식, CA 파일 존재, Keystone TLS 선행 조건을 확인합니다. validate는 원본 50개 항목의 설정값인 `auth_strategy`, `auth_url` scheme, `insecure=false`, `max_request_body_size`, `admin_token` 제거 등을 확인합니다. OpenStack 설정 파일 권한 hardening과 Horizon cookie 검증은 원본 50개 밖 확장 항목으로 기본 실행에서 제외합니다.

## Verification Strategy

| 검증 계층 | 명령 또는 방법 | 목적 |
| --- | --- | --- |
| Syntax | `ansible-playbook --syntax-check playbooks/security-policy-2026.yml -i inventory/security-policy-2026.example.ini` | 통합 playbook 문법 확인 |
| Lint | `ansible-lint` | FQCN, idempotency, YAML, risky task 패턴 확인 |
| Project Molecule | `molecule test -s project-syntax` | role test playbook, 통합 playbook, Molecule converge/verify playbook syntax smoke |
| Delegated Molecule | `MOLECULE_TARGET_HOST=<host> molecule verify -s <scenario>` | 실제 DB/Docker/Kubernetes/OpenStack 대상 노드에서 smoke 검증 |
| Docker Molecule | `molecule test -s docker-security-docker` | Docker role 컨테이너 기반 검증. Docker daemon 접근 필요 |

Delegated 시나리오인 `db-security`, `docker-security`, `k8s-security`, `openstack-component`는 외부 VM/노드가 있어야 실제 verify가 가능합니다. 대상은 `MOLECULE_TARGET_HOST`, `MOLECULE_TARGET_USER`, `MOLECULE_TARGET_PRIVATE_KEY_FILE` 환경 변수로 지정합니다.
