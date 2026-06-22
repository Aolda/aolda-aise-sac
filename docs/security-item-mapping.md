# Security Item Mapping

이 문서는 현재 Ansible 보안 자동화 구현을 원본 담당 보안 항목 50개 기준으로 다시 매핑한 문서입니다. 세부 task, validate, precheck, backup, handler는 원본 항목 수에 포함하지 않고 각 항목의 세부 조치 또는 추가 구현/운영 안정성 보강 항목으로 분리합니다.

상태 값은 아래 기준을 사용합니다.

| 상태 | 의미 |
| --- | --- |
| `자동 조치` | 기본 실행 시 안전하게 적용되는 원본 보안 항목 |
| `점검 중심` | 기본 실행에서 자동 변경하지 않고 점검/경고/권고 중심으로 수행하는 항목 |
| `기본 비활성` | 구현되어 있으나 운영 영향 때문에 명시 변수 활성화 시에만 적용되는 항목 |
| `수동 필요` | 환경별 준비, 승인, 수동 절차가 필요한 항목 |
| `예외 처리` | 자동 일괄 적용하지 않는 예외 항목 |
| `미구현` | 원본에는 있으나 현재 코드에 구현이 없는 항목 |

# 원본 50개 항목 기준 구현 매핑

| ID | 영역 | 컴포넌트 | 원본 보안 항목 | 구현 방향 | 세부 구현 내용 | 관련 파일 | 기본 적용 여부 | 우리 환경 확인 사항 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| DB-01 | DB | MariaDB/MySQL | 불필요 DB 계정 제거 | `자동 조치` | 전체 허용 목록 방식으로 알 수 없는 계정을 삭제하지 않음. anonymous, test/guest, 운영자가 명시한 불필요 계정, 허용되지 않은 user@host 조합만 제거하고 DB Account Report로 미분류 계정을 안내. 삭제 보호 목록은 `db_account_delete_protected_users` 계열 변수로, 권한 회수 예외는 `db_privilege_exempt_users`로 분리 | `roles/db-security/tasks/1_accounts_password.yml` | 적용 또는 목록 기반 조건부 적용 | 서비스 계정, 백업 계정, DBA 계정이 제거 대상에 포함되지 않는지 확인하고 환경별 삭제 보호 목록에 추가 |
| DB-02 | DB | MariaDB/MySQL | 취약한 패스워드 사용 제한 | `점검 중심` | DB 종류와 버전을 감지하고 지원 정책을 안내. 실제 `simple_password_check`/`validate_password` 설정과 component 설치는 `db_apply_password_policy=true`일 때만 수행 | `roles/db-security/tasks/0_detect_version.yml`, `roles/db-security/tasks/1_accounts_password.yml` | 기본 점검/권고. 강제 적용 비활성 | MySQL/MariaDB 버전, plugin/component 지원 여부, 기존 암호 정책 충돌 확인 |
| DB-03 | DB | MariaDB/MySQL | 타 사용자에 권한 부여 옵션 제한 | `자동 조치` | 일반 사용자가 다른 사용자에게 권한을 재위임하지 못하도록 GRANT OPTION을 회수. 예외 계정 변수 유지 | `roles/db-security/tasks/2_privileges.yml` | `db_regular_users` 목록 기반 조건부 적용 | 운영 DBA 계정과 자동화 계정은 예외 목록에 포함 |
| DB-04 | DB | MariaDB/MySQL | DB 사용자 계정 정보 테이블 접근 권한 제한 | `자동 조치` | 일반 사용자에게서 `mysql.user` 직접 접근 권한을 회수해 계정/해시 정보 노출을 줄임. 모니터링 계정 예외 가능 | `roles/db-security/tasks/2_privileges.yml` | `db_regular_users` 목록 기반 조건부 적용 | Prometheus exporter, 모니터링 계정의 필요 권한 확인 |
| DB-05 | DB | MariaDB/MySQL | root 권한으로 서버 구동 제한 | `점검 중심` | 기본 실행에서는 DB 프로세스 실행 계정을 점검하고 warning으로 안내. 설정 파일의 런타임 사용자 강제 변경은 `db_enforce_runtime_user=true`일 때만 수행 | `roles/db-security/tasks/3_root_and_logging.yml`, `roles/db-security/tasks/validate.yml` | 기본 점검/권고. 강제 변경 비활성 | 실제 DB 프로세스 실행 계정, systemd unit, 컨테이너 DB 여부 확인 |
| DB-06 | DB | MariaDB/MySQL | 환경설정 파일 접근 권한 제한 | `자동 조치` | DB 설정 파일을 root/mysql 소유와 0640 이하 권한으로 관리 | `roles/db-security/tasks/3_root_and_logging.yml` | 적용 | OS별 설정 파일 경로와 group 소유권 확인 |
| DB-07 | DB | MariaDB/MySQL | 안전한 패스워드 암호화 알고리즘 사용 | `기본 비활성` | 기본 인증 플러그인과 계정별 인증 플러그인 변경 기능은 제공하되 DB 종류/버전/클라이언트 호환성 때문에 기본 적용하지 않음 | `roles/db-security/tasks/4_authentication_and_patch.yml` | 비활성 | MySQL 8, MariaDB, 클라이언트 드라이버의 인증 플러그인 호환성 확인 |
| DB-08 | DB | MariaDB/MySQL | 로그 활성화 | `자동 조치` | slow_query_log와 error log 중심으로 설정. general_log는 강제하지 않으며 이미 켜져 있어도 기본 fail하지 않고 warning/debug 처리 | `roles/db-security/tasks/3_root_and_logging.yml`, `roles/db-security/tasks/validate.yml` | slow/error log 적용, general_log 예외 | 로그 경로, 디스크 용량, 보관 정책, general_log 사용 정책 확인 |
| DB-09 | DB | MariaDB/MySQL | 최신 보안 패치 적용 | `예외 처리` | 패키지 업데이트는 기본 비활성이고 `state: present` 중심으로 관리. latest는 명시 변수로만 선택 | `roles/db-security/tasks/4_authentication_and_patch.yml` | 비활성 | 패치 윈도우, DB 버전 고정 정책, 롤백 계획 확인 |
| DOCKER-01 | Docker | Docker Engine | 도커 최신 보안 패치 적용 | `예외 처리` | Docker Engine 업데이트는 컨테이너 재시작과 런타임 변경 위험이 있어 기본 자동 적용하지 않음 | `roles/docker-security/tasks/1_version_and_users.yml` | 비활성 | Kolla/OpenStack 컨테이너 재기동 영향, 패치 윈도우 확인 |
| DOCKER-02 | Docker | Docker Group | 도커 그룹에 불필요한 사용자 제거 | `자동 조치` | docker 그룹 생성, 허용 사용자 관리, `docker_disallowed_group_users` 제거를 한 원본 항목의 세부 구현으로 처리 | `roles/docker-security/tasks/1_version_and_users.yml` | 적용 또는 목록 기반 조건부 적용 | `kolla`, `ansible`, 운영 자동화 계정 필요 여부 확인 |
| DOCKER-03 | Docker | Runtime | Host의 user namespaces 공유 제한 | `점검 중심` | 컨테이너의 `HostConfig.UsernsMode == host` 여부를 점검하고 기본은 warning 출력 | `roles/docker-security/tasks/5_container_runtime_checks.yml` | 점검만 수행 | host user namespace 공유가 필요한 컨테이너 예외 확인 |
| DOCKER-04 | Docker | Audit | Docker daemon audit 설정 | `기본 비활성` | auditd 설치, Docker 관련 경로 audit rule 등록, audit rules 파일 권한 지정을 세부 구현으로 포함 | `roles/docker-security/tasks/2_audit_config.yml` | 비활성 | auditd 사용 정책, 로그 수집 체계, rule 중복, auditd 재시작 정책 확인 |
| DOCKER-05 | Docker | Runtime | 추가 권한 획득으로부터 컨테이너 제한 | `점검 중심` | `no-new-privileges:true` 누락 여부를 점검하되 기존 컨테이너를 자동 수정하지 않음 | `roles/docker-security/tasks/5_container_runtime_checks.yml` | 점검만 수행 | 권한 상승이 필요한 컨테이너 존재 여부 확인 |
| DOCKER-06 | Docker | `docker.service` | docker.service 소유권 설정 | `자동 조치` | docker service unit 파일 소유자를 root 계열로 제한 | `roles/docker-security/tasks/3_file_permissions.yml` | 파일 존재 시 적용 | unit 파일 실제 위치가 `/lib` 또는 `/usr/lib`인지 확인 |
| DOCKER-07 | Docker | `docker.service` | docker.service 파일 접근 권한 설정 | `자동 조치` | docker service unit 파일 mode를 role 기준으로 제한 | `roles/docker-security/tasks/3_file_permissions.yml` | 파일 존재 시 적용 | 패키지 업데이트가 unit 권한을 되돌릴 수 있는지 확인 |
| DOCKER-08 | Docker | `docker.socket` | docker.socket 소유권 설정 | `자동 조치` | docker socket unit 파일 소유자를 root 계열로 제한 | `roles/docker-security/tasks/3_file_permissions.yml` | 파일 존재 시 적용 | socket activation 사용 여부 확인 |
| DOCKER-09 | Docker | `docker.socket` | docker.socket 파일 접근 권한 설정 | `자동 조치` | docker socket unit 파일 mode를 role 기준으로 제한 | `roles/docker-security/tasks/3_file_permissions.yml` | 파일 존재 시 적용 | Docker socket activation과 운영 도구 영향 확인 |
| DOCKER-10 | Docker | `/etc/docker` | /etc/docker 소유권 설정 | `자동 조치` | Docker 설정 디렉터리 owner/group을 제한 | `roles/docker-security/tasks/3_file_permissions.yml` | 적용 | Kolla 또는 설정 관리 도구가 해당 디렉터리를 쓰는지 확인 |
| DOCKER-11 | Docker | `/etc/docker` | /etc/docker 파일 접근 권한 설정 | `자동 조치` | Docker 설정 디렉터리 mode를 제한해 설정 노출/변조를 방지 | `roles/docker-security/tasks/3_file_permissions.yml` | 적용 | daemon.json, certs.d 등 하위 경로 접근 필요성 확인 |
| DOCKER-12 | Docker | `docker.sock` | /var/run/docker.sock 소유권 설정 | `자동 조치` | Docker API socket owner/group을 제한 | `roles/docker-security/tasks/3_file_permissions.yml` | socket 존재 시 적용 | Kolla, monitoring, CI agent의 socket 접근 권한 확인 |
| DOCKER-13 | Docker | `docker.sock` | /var/run/docker.sock 파일 접근 권한 설정 | `자동 조치` | Docker API socket mode를 제한해 일반 사용자 접근을 방지 | `roles/docker-security/tasks/3_file_permissions.yml` | socket 존재 시 적용 | socket 권한 변경 시 운영 자동화 영향 확인 |
| DOCKER-14 | Docker | `daemon.json` | daemon.json 소유권 설정 | `자동 조치` | daemon.json이 존재할 때 owner/group을 root 계열로 제한 | `roles/docker-security/tasks/3_file_permissions.yml` | 파일 존재 시 적용 | daemon.json이 Kolla 또는 배포 도구에 의해 관리되는지 확인 |
| DOCKER-15 | Docker | `daemon.json` | daemon.json 파일 접근 권한 설정 | `자동 조치` | daemon.json이 존재할 때 mode를 `docker_daemon_config_mode`로 제한 | `roles/docker-security/tasks/3_file_permissions.yml` | 파일 존재 시 적용 | registry, log-driver, live-restore 등 기존 설정 노출 여부 확인 |
| DOCKER-16 | Docker | Image Trust | 도커를 위한 컨텐츠 신뢰성 활성화 | `예외 처리` | profile 파일로 `DOCKER_CONTENT_TRUST=1` 설정은 가능하지만 사용자 shell, CI, registry workflow까지 강제할 수 없어 기본 비활성 | `roles/docker-security/tasks/1_version_and_users.yml` | 비활성 | 이미지 서명 정책, private registry, CI pull/push 방식 확인 |
| DOCKER-17 | Docker | Runtime | 컨테이너 SELinux 보안 옵션 설정 | `점검 중심` | SELinux 적용 여부를 런타임 점검 대상으로만 보고 자동 변경하지 않음 | `roles/docker-security/tasks/5_container_runtime_checks.yml` | 점검만 수행 | 호스트 SELinux mode, Docker SELinux 지원 여부 확인 |
| DOCKER-18 | Docker | Runtime | 컨테이너에서 SSH 사용 금지 | `점검 중심` | 컨테이너 프로세스에서 `sshd` 패턴을 점검하고 warn/fail 모드로 보고 | `roles/docker-security/tasks/5_container_runtime_checks.yml` | 점검만 수행 | 디버그용 SSH 컨테이너, 운영 예외 컨테이너 확인 |
| DOCKER-19 | Docker | Runtime | 컨테이너에 privileged 포트 매핑 금지 | `점검 중심` | privileged host port 매핑을 점검하고 기본은 warning 출력 | `roles/docker-security/tasks/5_container_runtime_checks.yml` | 점검만 수행 | 1024 미만 포트를 직접 사용하는 컨테이너 예외 확인 |
| DOCKER-20 | Docker | Runtime | PIDs cgroup 제한 | `점검 중심` | 컨테이너별 PidsLimit을 점검하되 일괄 제한하지 않음 | `roles/docker-security/tasks/5_container_runtime_checks.yml` | 점검만 수행 | 컨테이너별 정상 PID 사용량과 예외 확인 |
| K8S-01 | Kubernetes | Control Plane | Control Plane 파일 및 PKI 권한 보호 | `점검 중심` | 기본 모드는 파일 존재/권한 상태 점검과 report 중심. 실제 chmod/chown과 controller-manager 보안 인자는 `k8s_apply_control_plane=true`일 때만 적용 | `roles/k8s-security/tasks/precheck.yml`, `roles/k8s-security/tasks/1_control_plane.yml` | 기본 점검. 수정 비활성 | control-plane 노드 구분, `/etc/kubernetes` 경로, 인증서 권한 백업 확인 |
| K8S-02 | Kubernetes | API Server | API 서버 인증·인가 및 감사 로깅 설정 | `점검 중심` | 기본 모드는 anonymous-auth, authorization-mode, token-auth-file, audit log, Admission Plugin, TLS 상태를 report. manifest 수정은 `k8s_apply_api_server=true` 등 고급 변수 필요 | `roles/k8s-security/tasks/2_api_server.yml`, `roles/k8s-security/tasks/validate.yml` | 기본 점검. 수정 비활성 | kube-apiserver manifest 백업, Kubernetes 버전, audit 저장소, admission plugin 호환성 확인 |
| K8S-03 | Kubernetes | etcd | etcd 저장 데이터 암호화 및 TLS 보호 | `수동 필요` | encryption-provider-config, TLS 인증서 존재 여부, etcd 데이터 디렉터리 권한 상태를 점검. 암호화/TLS/권한 변경은 각각 명시 변수 활성화 시에만 적용하며 기존 Secret 재암호화는 자동 실행하지 않음 | `roles/k8s-security/tasks/3_etcd.yml`, `roles/k8s-security/tasks/validate.yml`, `docs/architecture.md` | 기본 점검. 변경 비활성 | etcd snapshot, Secret 재암호화 절차, etcd 인증서 7개, 데이터 디렉터리 권한 확인 |
| K8S-04 | Kubernetes | Kubelet | kubelet 인증·인가 및 TLS 설정 | `점검 중심` | 기본 모드는 kubelet anonymous-auth, authorization, TLS cipher, protectKernelDefaults 상태를 report. 자동 수정은 `k8s_apply_kubelet=true`일 때만 수행 | `roles/k8s-security/tasks/4_kubelet.yml`, `roles/k8s-security/tasks/validate.yml` | 기본 점검. 수정 비활성 | worker별 kubelet config 위치, cipher 지원, kubelet 재시작 영향 확인 |
| K8S-05 | Kubernetes | Policy | RBAC·Pod 보안·NetworkPolicy·시크릿 관리 | `점검 중심` | PSA/PSS, RBAC, NetworkPolicy, default ServiceAccount token, Secret/Pod 템플릿과 기존 Pod 보안 상태를 점검 중심으로 관리하고 적용은 명시 변수 필요 | `roles/k8s-security/tasks/5_policies.yml`, `roles/k8s-security/tasks/6_pod_security_checks.yml` | 기본 점검. 실제 적용은 비활성 | CNI NetworkPolicy 지원, namespace별 workload, Pod securityContext, Secret 관리 방식 확인 |
| OSAUTH-01 | OpenStack 인증/인가 | Keystone | Keystone TLS 설정 | `기본 비활성` | Keystone ssl section에 enable, certfile, keyfile, ca_certs를 설정하는 기능은 있으나 기본 모드에서는 인증서/CA/endpoint 상태만 precheck | `roles/keystone-security/tasks/precheck.yml`, `roles/keystone-security/tasks/main.yml` | 비활성 | 인증서/key/CA 파일, HTTPS endpoint, endpoint catalog 전환 계획 확인 |
| OSAUTH-02 | OpenStack 인증/인가 | Keystone | Keystone PKI token hash 알고리즘 강화 | `자동 조치` | token section의 `hash_algorithm`을 강한 알고리즘으로 설정 | `roles/keystone-security/tasks/main.yml` | 적용 | Keystone 버전에서 PKI token 설정 사용 여부 확인 |
| OSAUTH-03 | OpenStack 인증/인가 | Keystone | Keystone max_request_body_size 설정 | `자동 조치` | oslo_middleware section에 요청 본문 최대 크기 제한을 설정 | `roles/keystone-security/tasks/main.yml` | 적용 | API client의 대용량 요청 영향 확인 |
| OSAUTH-04 | OpenStack 인증/인가 | Keystone | Keystone admin_token 비활성화 | `자동 조치` | DEFAULT section의 legacy `admin_token`을 제거. bootstrap 스크립트 영향은 운영자가 확인 | `roles/keystone-security/tasks/main.yml` | 적용 | 기존 운영 스크립트가 admin_token에 의존하지 않는지 확인 |
| OSAUTH-05 | OpenStack 인증/인가 | Nova | Compute 인증을 위한 보안 프로토콜 사용 | `기본 비활성` | Nova keystone_authtoken의 auth_uri, auth_url, cafile, insecure=false 설정 기능은 있으나 Keystone TLS 선행 확인 후에만 선택 적용 | `roles/nova-security/tasks/precheck.yml`, `roles/nova-security/tasks/main.yml` | 비활성 | Keystone TLS 선행 완료, CA trust, endpoint scheme 확인 |
| OSAUTH-06 | OpenStack 인증/인가 | Nova | Nova와 Glance의 안전한 통신 | `기본 비활성` | glance section의 api_servers, cafile, insecure=false 설정 기능은 있으나 Glance HTTPS 전환 후 선택 적용 | `roles/nova-security/tasks/main.yml` | 비활성 | Glance HTTPS endpoint와 image 서비스 연결 영향 확인 |
| OSAUTH-07 | OpenStack 인증/인가 | Nova | Compute의 인증을 위한 Keystone 사용 | `자동 조치` | `auth_strategy`가 비어 있거나 `noauth`이면 `keystone`으로 설정 | `roles/nova-security/tasks/main.yml` | 조건부 적용 | 현재 Nova auth_strategy와 noauth 의존 여부 확인 |
| OSAUTH-08 | OpenStack 인증/인가 | Cinder | 블록스토리지 서비스 인증을 위한 TLS 활성화 | `기본 비활성` | Cinder keystone_authtoken의 auth_uri, auth_url, cafile, insecure=false 설정 기능은 있으나 Keystone TLS 선행 확인 후 선택 적용 | `roles/cinder-security/tasks/precheck.yml`, `roles/cinder-security/tasks/main.yml` | 비활성 | Keystone TLS 선행 완료, CA trust 확인 |
| OSAUTH-09 | OpenStack 인증/인가 | Cinder | Cinder와 Nova의 TLS 통신 | `기본 비활성` | nova section의 auth_url, cafile, insecure=false 설정 기능은 있으나 Nova HTTPS endpoint 준비 후 선택 적용 | `roles/cinder-security/tasks/main.yml` | 비활성 | Nova HTTPS endpoint, CA trust, API 호환성 확인 |
| OSAUTH-10 | OpenStack 인증/인가 | Cinder | Cinder와 Glance의 TLS 통신 | `기본 비활성` | glance_api_servers, glance_ca_certificates_file, glance_api_insecure 설정 기능은 있으나 Glance HTTPS endpoint 준비 후 선택 적용 | `roles/cinder-security/tasks/main.yml` | 비활성 | Glance HTTPS endpoint, CA trust, image API 호환성 확인 |
| OSAUTH-11 | OpenStack 인증/인가 | Cinder | 블록 스토리지 서비스의 인증을 위한 Keystone 사용 | `자동 조치` | `auth_strategy`가 비어 있거나 `noauth`이면 `keystone`으로 설정 | `roles/cinder-security/tasks/main.yml` | 조건부 적용 | 현재 Cinder auth_strategy와 noauth 의존 여부 확인 |
| OSAUTH-12 | OpenStack 인증/인가 | Cinder | 블록 스토리지 서비스에서 요청 본문 최대 크기 설정 | `자동 조치` | oslo_middleware section에 요청 본문 최대 크기 제한을 설정 | `roles/cinder-security/tasks/main.yml` | 적용 | 볼륨 API 요청 크기 정책 확인 |
| OSAUTH-13 | OpenStack 인증/인가 | Glance | 이미지스토리지 서비스 인증을 위한 TLS 활성화 | `기본 비활성` | Glance keystone_authtoken의 auth_uri, auth_url, cafile, insecure=false 설정 기능은 있으나 Keystone HTTPS 확인 후 선택 적용 | `roles/glance-security/tasks/precheck.yml`, `roles/glance-security/tasks/main.yml` | 비활성 | Keystone HTTPS endpoint와 CA 파일 확인 |
| OSAUTH-14 | OpenStack 인증/인가 | Glance | 이미지 스토리지 서비스 인증을 위한 Keystone 설정 | `자동 조치` | paste_deploy section의 `flavor=keystone` 설정 | `roles/glance-security/tasks/main.yml` | 적용 | Glance pipeline과 Keystone middleware 구성 확인 |
| OSAUTH-15 | OpenStack 인증/인가 | Neutron | 네트워킹 서비스의 인증을 위한 안전한 프로토콜 사용 | `기본 비활성` | Neutron keystone_authtoken의 auth_uri, auth_url, cafile, insecure=false 설정 기능은 있으나 Keystone TLS 선행 확인 후 선택 적용 | `roles/neutron-security/tasks/precheck.yml`, `roles/neutron-security/tasks/main.yml` | 비활성 | Keystone TLS 선행 완료, CA trust 확인 |
| OSAUTH-16 | OpenStack 인증/인가 | Neutron | Neutron API 서버 TLS 설정 | `기본 비활성` | DEFAULT section의 `bind_ssl=true`, `use_ssl=true` 설정 기능은 있으나 endpoint/LB/proxy 검토 후 선택 적용 | `roles/neutron-security/tasks/main.yml` | 비활성 | Neutron endpoint, LB/proxy, agent 연결 영향 확인 |

# 원본 50개 외 추가 구현/운영 안정성 보강 항목

## 1) 유지하는 운영 안정성 보조 로직

| 항목 | 기존 위치 | 원본 50개 포함 여부 | 처리 결과 | 이유 |
| --- | --- | --- | --- | --- |
| precheck | `roles/*-security/tasks/precheck.yml`, `roles/k8s-security/tasks/precheck.yml` | 미포함 | 유지 | 설정 파일, 인증서, endpoint, 노드 역할을 먼저 확인해야 원본 50개 항목을 안전하게 분기 적용할 수 있음 |
| backup | 각 role의 `ini_file`, `copy`, `lineinfile` task | 미포함 | 유지 | 설정 변경 전 복구 지점을 남기는 운영 안전장치이며 별도 보안 목적 항목이 아님 |
| validate | `roles/*-security/tasks/validate.yml` | 미포함 | 유지 | 적용 결과와 drift를 확인하기 위한 검증 구조이며 DB validate도 원본 항목 수로 세지 않음 |
| handler | `roles/*-security/handlers/main.yml` | 미포함 | 유지 | 서비스 재시작을 변경 발생 시점과 명시 변수로 통제하기 위한 구조 |
| Kubernetes control-plane/worker 노드 역할 감지 | `roles/k8s-security/tasks/precheck.yml` | 미포함 | 유지 | worker에서 control-plane 파일 부재로 실패하지 않도록 원본 K8S-01~05 적용 대상을 구분 |
| Kubernetes YAML 검증 | `roles/k8s-security/tasks/precheck.yml`, `roles/k8s-security/tasks/validate.yml` | 미포함 | 유지 | static pod manifest 수정 시 YAML 손상을 방지하는 안전 검증 |
| Docker warn/fail 모드 | `roles/docker-security/tasks/5_container_runtime_checks.yml` | 미포함 | 유지 | DOCKER-03/05/17/18/19/20 점검 결과를 운영자가 warning 또는 fail로 선택하게 하는 보고 강도 제어 |

## 2) 제거 또는 제외한 원본 외 보안 항목

| 항목 | 기존 위치 | 원본 50개 포함 여부 | 처리 결과 | 이유 |
| --- | --- | --- | --- | --- |
| OpenStack 설정 파일 권한 hardening | `roles/keystone-security/tasks/permissions.yml`, `roles/nova-security/tasks/main.yml`, `roles/cinder-security/tasks/main.yml`, `roles/glance-security/tasks/main.yml`, `roles/neutron-security/tasks/main.yml` | 미포함 | 기본 실행 제외. `*_security_manage_config_permissions=false` 기본값으로 잠금 | 원본 OpenStack 16개는 인증/인가, TLS, 요청 크기, admin token 중심이므로 conf 권한 hardening은 별도 보안 목적 항목으로 분리 |
| Horizon Secure Cookie | `roles/horizon-security/tasks/main.yml` | 미포함 | 기본 playbook 실행 제외 | Horizon/ACC는 원본 OpenStack 인증/인가 16개에 포함되지 않고 HTTPS 선행 조건이 필요함 |
| Horizon password validator | `roles/horizon-security/tasks/main.yml` | 미포함 | 기본 playbook 실행 제외 | Dashboard 비밀번호 정책은 원본 50개 밖의 별도 보안 목적 항목임 |
| Cinder volume encryption | `roles/cinder-security/tasks/volume_encryption.yml` | 미포함 | 기본 실행 제외. `cinder_security_include_volume_encryption_extension=false` 기본값으로 잠금 | Barbican/KMS, volume type, 기존 볼륨 영향 검토가 필요한 별도 프로젝트 범위 |
| Docker daemon.json 보안 옵션 병합 | `roles/docker-security/tasks/4_daemon_security.yml` | 미포함 | 기본 실행 제외. `docker_enable_daemon_config_extension=false` 기본값으로 잠금 | DOCKER-14/15는 daemon.json 소유권/권한 항목이며 daemon 옵션 병합은 추가 보안 목적 항목임 |
| Neutron auth_strategy 추가 보강 | `roles/neutron-security/tasks/main.yml` | 미포함 | 기본 실행 제외. `neutron_security_manage_auth_strategy_extension=false` 기본값으로 잠금 | 원본 OSAUTH-15/16은 Neutron Keystone 통신 TLS와 API TLS 항목이므로 auth_strategy 변경은 별도 보강으로 분리 |
| Kubernetes 안전한 Pod/Secret 템플릿 생성 | `roles/k8s-security/tasks/5_policies.yml` | 미포함 | 기본 비활성 유지 | 원본 K8S-05의 점검/가이드 세부 조치로만 다루며 workload manifest 자동 적용은 하지 않음 |
| DB 인증 플러그인 계정별 변경 | `roles/db-security/tasks/4_authentication_and_patch.yml` | 원본 DB-07 세부 구현과 연계 | 기본 비활성 유지 | DB 종류/버전/클라이언트 호환성 영향이 커 명시 변수와 대상 계정 지정 시에만 적용 |
| Molecule 및 syntax smoke | `molecule/*`, `docs/molecule-testing.md` | 미포함 | 유지 | 보안 목적 항목이 아니라 프로젝트 검증 체계 |

# 최종 summary

| 영역 | 원본 항목 수 | 구현/반영 완료 | 기본 비활성 | 점검 전용 | 예외/수동 | 미구현 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| DB | 9 | 5 | 1 | 2 | 1 | 0 |
| Docker | 20 | 11 | 1 | 6 | 2 | 0 |
| Kubernetes | 5 | 0 | 0 | 4 | 1 | 0 |
| OpenStack 인증/인가 | 16 | 7 | 9 | 0 | 0 | 0 |
| 합계 | 50 | 23 | 11 | 12 | 4 | 0 |

요약하면 원본 담당 항목 50개는 모두 현재 코드에 매핑되어 있습니다. 원본 50개를 안전하게 실행하기 위한 precheck, backup, validate, handler, 노드 역할 감지, YAML 검증, warn/fail 모드는 유지하고, 원본에 없는 Horizon, Cinder volume encryption, Docker daemon 옵션 병합, Neutron auth_strategy 추가 보강, OpenStack 설정 파일 권한 hardening은 기본 실행에서 제외했습니다.
