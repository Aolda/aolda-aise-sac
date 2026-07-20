# Operational Variable Checklist

이 문서는 실제 운영환경에 보안 playbook을 적용하기 전에 운영자가 확인하거나 채워야 하는 변수만 별도로 정리합니다. 단순 defaults 나열이 아니라, 실제 서버에서 확인해야 하는 경로, endpoint, 인증서, 계정 목록, 서비스명, kubeconfig, Docker/Kubernetes/OpenStack 구성값 기준으로 분류합니다.

현재 저장소에는 `group_vars/.gitkeep`만 있고 실제 `group_vars/*.yml`, `host_vars/` 값은 아직 없습니다. 운영 반영 전 이 문서를 기준으로 inventory별 변수를 작성하세요.

## 1. 전체 요약

| 분류 | 개수 | 의미 |
| --- | ---: | --- |
| A. 기본값 그대로 사용 가능 | 31 | mode, 기본 false 플래그, warn/report 모드처럼 대부분 유지 가능한 값 |
| B. 운영환경에서 반드시 확인해야 하는 값 | 46 | 서버별 파일 경로, 서비스명, endpoint, 인증서, kubeconfig, socket 등 |
| C. 운영환경별 추가 목록으로 관리해야 하는 값 | 20 | DB 계정 목록, Docker 사용자, Kubernetes namespace 등 환경별 목록 |
| D. 위험해서 기본 비활성 유지가 필요한 값 | 34 | true 전환 전 백업/점검/승인이 필요한 변경 플래그 |

위 개수는 아래 표에 명시한 변수 또는 변수 그룹 기준입니다. 반복되는 OpenStack 컴포넌트 변수는 역할별로 따로 계산했습니다.

**위험도가 높은 변수**

- 매우 높음: `db_unnecessary_accounts`, `db_disallowed_account_hosts`, `db_apply_password_policy`, `db_apply_security_patch`, `k8s_apply_api_server`, `k8s_apply_etcd_tls`, `k8s_apply_etcd_encryption_config`, `k8s_apply_kubelet`, `k8s_restart_kubelet`, `*_security_enable_tls`, `*_security_restart_service`
- 높음: `db_config_file`, `db_login_unix_socket`, `db_runtime_user`, `db_runtime_group`, `docker_daemon_config`, `docker_restart_service`, OpenStack `*_security_config_file`, OpenStack endpoint/CA 변수

**사전 확인 없이 true로 바꾸면 안 되는 변수**

`db_apply_password_policy`, `db_enable_validate_password_component`, `db_apply_security_patch`, `db_enforce_runtime_user`, `db_set_default_authentication_plugin`, `docker_apply_package_update`, `docker_apply_daemon_security`, `docker_enable_daemon_config_extension`, `docker_apply_audit_config`, `docker_restart_service`, `docker_restart_auditd`, `k8s_apply_control_plane`, `k8s_apply_api_server`, `k8s_apply_etcd_tls`, `k8s_apply_etcd_encryption_config`, `k8s_apply_etcd_permissions`, `k8s_apply_kubelet`, `k8s_apply_policies`, `k8s_apply_admission_plugins`, `k8s_restart_kubelet`, `k8s_enable_audit_log`, `k8s_manage_audit_policy_file`, `k8s_manage_encryption_config_file`, `k8s_apply_psa_labels`, `k8s_enable_rbac_controls`, `k8s_enable_network_policies`, `k8s_enable_secret_controls`, `keystone_security_enable_tls`, `nova_security_enable_tls`, `cinder_security_enable_tls`, `glance_security_enable_tls`, `neutron_security_enable_tls`, `*_security_restart_service`.

### 빠른 분류 목록

**A. 기본값 그대로 사용 가능**

대부분 운영에서도 유지 가능한 값입니다. 단, 조직 표준과 충돌하면 group_vars에서 조정합니다.

- 공통 검증: `*_validate_after_apply: true`
- 파일 권한: `db_max_config_file_mode: "0640"`, `docker_audit_rules_file_mode: "0640"`, OpenStack `*_security_config_mode: "0640"`
- 기본 false 안전 플래그: `*_restart_service: false`, `*_enable_tls: false`, `db_apply_password_policy: false`, `docker_apply_package_update: false`, `k8s_apply_*: false`
- report/warn 모드: `db_process_check_mode: warn`, `docker_runtime_check_mode: warn`, `docker_fail_on_runtime_policy_violation: false`, `k8s_fail_on_policy_violation: false`
- 일반 보안 기준값: `keystone_security_max_request_body_size: 114688`, `cinder_security_max_request_body_size: 114688`, `keystone_security_pki_hash_algorithm: sha256`

**B. 운영환경에서 반드시 확인해야 하는 값**

파일/디렉터리/서비스/endpoint/socket/kubeconfig/CA 경로입니다. 아래 영역별 표에서 `실제 운영환경에서 확인해야 하는 값`을 채워야 합니다.

- DB: `db_config_file`, `db_login_unix_socket`, `db_service_name`, `db_runtime_user`, `db_runtime_group`, 로그 경로
- OpenStack: `*_security_config_file`, `*_security_service_name`, `*_security_openrc_path`, TLS endpoint, CA/cert/key 파일
- Docker: service/socket unit 경로, `/etc/docker`, `daemon.json`, `/var/run/docker.sock`, audit rules 파일
- Kubernetes: manifest 경로, PKI 경로, etcd data/PKI, kubelet config, kubeconfig, audit/encryption config 경로

**C. 운영환경별 추가 목록으로 관리해야 하는 값**

코드에 하드코딩하지 말고 inventory, `group_vars`, `host_vars`에서 관리합니다.

- DB: `db_account_delete_protected_users_extra`, `db_privilege_exempt_users`, `db_regular_users`, `db_unnecessary_accounts`, `db_disallowed_account_hosts`
- Docker: `docker_allowed_users`, `docker_disallowed_group_users`, `docker_audit_watch_paths`, `docker_daemon_config`
- Kubernetes: `k8s_psa_namespace`, `k8s_network_policy_namespace`, `k8s_rbac_namespace`, `k8s_secret_namespace`, RBAC rule/ServiceAccount 이름
- OpenStack: TLS endpoint와 CA 경로, 컴포넌트별 서비스명, `*_security_cli_environment`

**D. 위험해서 기본 비활성 유지가 필요한 값**

아래 값은 true로 바꾸면 파일 수정, 서비스 재시작, 정책 강제, endpoint 전환 같은 운영 영향이 발생합니다.

- DB: `db_apply_password_policy`, `db_enable_validate_password_component`, `db_apply_security_patch`, `db_enforce_runtime_user`, `db_set_default_authentication_plugin`
- Docker: `docker_apply_package_update`, `docker_apply_daemon_security`, `docker_enable_daemon_config_extension`, `docker_apply_audit_config`, `docker_restart_service`, `docker_restart_auditd`
- Kubernetes: `k8s_apply_control_plane`, `k8s_apply_api_server`, `k8s_apply_etcd_tls`, `k8s_apply_etcd_encryption_config`, `k8s_apply_etcd_permissions`, `k8s_apply_kubelet`, `k8s_apply_policies`, `k8s_apply_admission_plugins`, `k8s_restart_kubelet`
- OpenStack: `keystone_security_enable_tls`, `nova_security_enable_tls`, `cinder_security_enable_tls`, `glance_security_enable_tls`, `neutron_security_enable_tls`, `*_security_restart_service`, `*_security_manage_config_permissions`

## 2. 영역별 운영 변수 목록

### DB

DB 계정 관리는 전체 allowlist 기반 삭제 방식이 아닙니다. 전체 허용 계정 목록을 만들지 말고, 아래처럼 분리해서 관리합니다.

- 삭제 대상 계정: `db_test_users`, `db_unnecessary_accounts`, `db_disallowed_account_hosts`
- 삭제 보호 계정: `db_account_delete_protected_users`, `db_account_delete_protected_users_extra`
- 권한 회수 대상: `db_regular_users`
- 권한 회수 예외: `db_privilege_exempt_users`
- 미분류 계정: 자동 삭제하지 않고 report/warning 대상으로 관리

민감한 password hash, `authentication_string`은 출력하지 마세요.

| 영역 | 변수명 | 현재 기본값 | 실제 운영환경에서 확인해야 하는 값 | 확인 방법/명령어 | 어디에 넣을지 | 위험도 | 비고 |
| -- | --- | ------ | ------------------- | --------- | ------- | --- | -- |
| DB | `db_config_file` | `/etc/my.cnf` | 실제 MariaDB/MySQL 설정 파일 | `ls -l /etc/my.cnf /etc/mysql/my.cnf /etc/mysql/mariadb.conf.d/50-server.cnf` | `group_vars/db.yml` 또는 host별 | 높음 | 잘못 지정하면 설정 변경/검증 실패 |
| DB | `db_login_unix_socket` | `/var/lib/mysql/mysql.sock` | 실제 DB socket 경로 | `mysqladmin variables \| grep socket`, `ss -xl \| grep mysql` | `group_vars/db.yml` | 높음 | 잘못되면 모든 DB query task 실패 |
| DB | `db_service_name` | `mariadb` | systemd 서비스명 | `systemctl list-units '*mariadb*' '*mysql*'` | `group_vars/db.yml` | 중간 | 재시작 handler 대상 |
| DB | `db_runtime_user` | `mysql` | DB 프로세스 실행 계정 | `ps -eo user,comm,args \| grep -E 'mysqld|mariadbd'` | `group_vars/db.yml` | 높음 | 강제 변경은 `db_enforce_runtime_user=true`일 때만 |
| DB | `db_runtime_group` | `mysql` | 설정/로그 파일 group | `id mysql`, `stat -c '%U %G %a' /etc/my.cnf` | `group_vars/db.yml` | 높음 | 파일 권한 task에 사용 |
| DB | `db_account_delete_protected_users` | `root`, `mysql`, `debian-sys-maint` | 기본 삭제 보호 계정 유지 여부 | `mysql -e "SELECT User, Host FROM mysql.user ORDER BY User, Host;"` | 기본값 또는 `group_vars/db.yml` | 매우 높음 | 기본 시스템 계정 보호 |
| DB | `db_account_delete_protected_users_extra` | `[]` | OpenStack 서비스, 백업, 모니터링, DBA, replication 계정 | `mysql -e "SELECT User, Host FROM mysql.user ORDER BY User, Host;"` | `group_vars/db.yml` | 매우 높음 | 환경별 추가 보호 목록 |
| DB | `db_include_privilege_exempt_users_in_delete_protection` | `true` | 권한 회수 예외를 삭제 보호에도 포함할지 여부 | 계정 운영 정책 검토 | 기본값 권장 | 중간 | 역할 분리는 유지됨 |
| DB | `db_privilege_exempt_users` | `prometheus`, `mysqld_exporter` | 권한 회수 예외 계정 | `mysql -e "SHOW GRANTS FOR 'prometheus'@'%';"` | `group_vars/db.yml` | 높음 | 삭제 예외가 아니라 권한 회수 예외 |
| DB | `db_regular_users` | `[]` | GRANT OPTION/mysql.user 권한 회수 대상 | `mysql -e "SELECT User, Host FROM mysql.user ORDER BY User, Host;"` | `group_vars/db.yml` | 높음 | 명시한 계정만 권한 회수 |
| DB | `db_unnecessary_accounts` | `[]` | 명시적으로 삭제할 불필요 계정 | `mysql -e "SELECT User, Host FROM mysql.user ORDER BY User, Host;"` | `group_vars/db.yml` | 매우 높음 | 보호 목록 충돌 시 fail |
| DB | `db_disallowed_account_hosts` | `[]` | 삭제할 특정 `user@host` 조합 | `mysql -e "SELECT User, Host FROM mysql.user ORDER BY User, Host;"` | `group_vars/db.yml` | 매우 높음 | host까지 정확히 확인 |
| DB | `db_apply_password_policy` | `false` | 패스워드 정책 강제 적용 여부 | DB 종류/버전, 앱 호환성 검토 | `group_vars/db.yml` | 매우 높음 | 기본 비활성 유지 권장 |
| DB | `db_password_policy_type` | `auto` | MariaDB/MySQL 정책 방식 | `mysql -e "SELECT @@VERSION, @@VERSION_COMMENT;"` | 기본값 또는 `group_vars/db.yml` | 중간 | 보통 `auto` 유지 |
| DB | `db_log_dir`, `db_slow_query_log_file`, `db_error_log_file` | `/var/log/mysql`, `/var/log/mysql/mariadb-slow.log`, `/var/log/mysql/error.log` | 로그 경로와 디스크 정책 | `ls -ld /var/log/mysql`, `df -h /var/log` | `group_vars/db.yml` | 중간 | 경로 없으면 role이 생성 |
| DB | `db_apply_security_patch` | `false` | DB 패키지 업데이트 여부 | 패치 윈도우, 복구 계획 확인 | `group_vars/db.yml` | 매우 높음 | 기본 비활성 유지 |

### OpenStack

OpenStack TLS는 endpoint catalog, 인증서/CA trust, LB/Proxy, 클라이언트 설정을 함께 바꾸는 작업입니다. TLS 변수는 기본 `false`를 유지하고 운영 전환 계획이 있을 때만 활성화하세요.

| 영역 | 변수명 | 현재 기본값 | 실제 운영환경에서 확인해야 하는 값 | 확인 방법/명령어 | 어디에 넣을지 | 위험도 | 비고 |
| -- | --- | ------ | ------------------- | --------- | ------- | --- | -- |
| OpenStack | `keystone_security_config_file` | `/etc/keystone/keystone.conf` | Keystone 설정 파일 | `ls -l /etc/keystone/keystone.conf` | `group_vars/keystone.yml` | 높음 | 없으면 precheck fail |
| OpenStack | `nova_security_config_file` | `/etc/nova/nova.conf` | Nova 설정 파일 | `ls -l /etc/nova/nova.conf` | `group_vars/nova.yml` | 높음 | compute/controller 배치 확인 |
| OpenStack | `cinder_security_config_file` | `/etc/cinder/cinder.conf` | Cinder 설정 파일 | `ls -l /etc/cinder/cinder.conf` | `group_vars/cinder.yml` | 높음 | storage/controller 배치 확인 |
| OpenStack | `glance_security_config_file` | `/etc/glance/glance-api.conf` | Glance API 설정 파일 | `ls -l /etc/glance/glance-api.conf` | `group_vars/glance.yml` | 높음 | 배포판별 경로 확인 |
| OpenStack | `neutron_security_config_file` | `/etc/neutron/neutron.conf` | Neutron 설정 파일 | `ls -l /etc/neutron/neutron.conf` | `group_vars/neutron.yml` | 높음 | network/controller 배치 확인 |
| OpenStack | `*_security_service_name` | `apache2`, `nova-api`, `cinder-api`, `glance-api`, `neutron-server` | 실제 systemd 서비스명 | `systemctl status apache2 nova-api cinder-api glance-api neutron-server` | 각 role group_vars | 중간 | RHEL 계열은 서비스명이 다를 수 있음 |
| OpenStack | `*_security_openrc_path` | `/root/admin-openrc` | OpenStack CLI 인증 파일 | `ls -l /root/admin-openrc`, `openstack token issue` | 각 role group_vars | 중간 | validate CLI task에 사용 |
| OpenStack | `keystone_security_enable_tls` | `false` | Keystone TLS 적용 여부 | TLS 전환 계획, endpoint catalog 확인 | `group_vars/keystone.yml` | 매우 높음 | true 전 사전 승인 필수 |
| OpenStack | `keystone_security_tls_endpoint_change_confirmed` | `false` | Keystone endpoint 전환 승인 | `openstack endpoint list` | `group_vars/keystone.yml` | 매우 높음 | TLS true일 때 precheck 조건 |
| OpenStack | `keystone_security_public_endpoint` | `""` | HTTPS Keystone endpoint | `openstack endpoint list \| grep keystone` | `group_vars/keystone.yml` | 매우 높음 | `https://` 필수 |
| OpenStack | `keystone_security_certfile`, `keystone_security_keyfile`, `keystone_security_cafile` | `/etc/keystone/ssl/...` | Keystone 서버 cert/key/CA 파일 | `ls -l <cert> <key> <ca>` | `group_vars/keystone.yml` | 매우 높음 | key 권한 특히 확인 |
| OpenStack | `keystone_security_ca_cert` | `""` | endpoint 검증용 CA path | `openssl s_client -connect <host>:5000 -showcerts` | `group_vars/keystone.yml` | 높음 | `uri` validate에 사용 |
| OpenStack | `nova_security_enable_tls` | `false` | Nova TLS 관련 설정 적용 | Keystone/Glance HTTPS 준비 확인 | `group_vars/nova.yml` | 매우 높음 | 기본 비활성 유지 |
| OpenStack | `nova_security_keystone_endpoint`, `nova_security_glance_endpoint` | `""`, `""` | Nova가 사용할 Keystone/Glance HTTPS endpoint | `openstack endpoint list` | `group_vars/nova.yml` | 매우 높음 | `https://` 필수 |
| OpenStack | `nova_security_ca_cert` | `""` | Nova가 신뢰할 CA 파일 | `ls -l <ca>` | `group_vars/nova.yml` | 높음 | TLS true일 때 필수 |
| OpenStack | `cinder_security_enable_tls` | `false` | Cinder TLS 관련 설정 적용 | Keystone/Nova/Glance HTTPS 준비 확인 | `group_vars/cinder.yml` | 매우 높음 | 기본 비활성 유지 |
| OpenStack | `cinder_security_keystone_endpoint`, `cinder_security_nova_endpoint`, `cinder_security_glance_endpoint` | `""` | Cinder가 사용할 HTTPS endpoints | `openstack endpoint list` | `group_vars/cinder.yml` | 매우 높음 | 모두 `https://` 필수 |
| OpenStack | `cinder_security_ca_cert` | `""` | Cinder가 신뢰할 CA 파일 | `ls -l <ca>` | `group_vars/cinder.yml` | 높음 | TLS true일 때 필수 |
| OpenStack | `glance_security_enable_tls` | `false` | Glance Keystone TLS 설정 적용 | Keystone HTTPS 준비 확인 | `group_vars/glance.yml` | 매우 높음 | 기본 비활성 유지 |
| OpenStack | `glance_security_keystone_endpoint`, `glance_security_ca_cert` | `""`, `""` | Glance가 사용할 Keystone endpoint/CA | `openstack endpoint list`, `ls -l <ca>` | `group_vars/glance.yml` | 매우 높음 | `https://` 필수 |
| OpenStack | `neutron_security_enable_tls` | `false` | Neutron TLS 설정 적용 | Keystone/Neutron API HTTPS 준비 확인 | `group_vars/neutron.yml` | 매우 높음 | 기본 비활성 유지 |
| OpenStack | `neutron_security_keystone_endpoint`, `neutron_security_api_endpoint`, `neutron_security_ca_cert` | `""` | Neutron Keystone/API endpoint와 CA | `openstack endpoint list`, `ls -l <ca>` | `group_vars/neutron.yml` | 매우 높음 | `https://` 필수 |
| OpenStack | `*_security_restart_service` | `false` | 설정 변경 후 서비스 재시작 여부 | 운영 영향/점검 창 확인 | 각 role group_vars | 매우 높음 | 기본값 유지 권장 |
| OpenStack | `*_security_manage_config_permissions` | `false` | conf 파일 권한 hardening 여부 | 패키지/배포 도구 소유권 정책 확인 | 각 role group_vars | 높음 | 원본 범위 밖 확장 |

### Docker

| 영역 | 변수명 | 현재 기본값 | 실제 운영환경에서 확인해야 하는 값 | 확인 방법/명령어 | 어디에 넣을지 | 위험도 | 비고 |
| -- | --- | ------ | ------------------- | --------- | ------- | --- | -- |
| Docker | `docker_group_name` | `docker` | Docker group 이름 | `getent group docker` | 기본값 또는 `group_vars/docker.yml` | 중간 | socket group에 사용 |
| Docker | `docker_allowed_users` | `root` | Docker group 유지 허용 사용자 | `getent group docker` | `group_vars/docker.yml` | 높음 | 운영 자동화 계정 확인 |
| Docker | `docker_disallowed_group_users` | `[]` | Docker group에서 제거할 사용자 | `getent group docker` | `group_vars/docker.yml` | 높음 | root급 권한 제거와 같음 |
| Docker | `docker_groups_to_clean` | `docker_group_name` | 정리 대상 group | `getent group docker` | 기본값 또는 `group_vars/docker.yml` | 중간 | 보통 기본값 유지 |
| Docker | `docker_service_unit_path` | `/lib/systemd/system/docker.service` | docker.service 실제 경로 | `ls -l /usr/lib/systemd/system/docker.service /lib/systemd/system/docker.service` | `group_vars/docker.yml` | 중간 | 배포판별 경로 차이 |
| Docker | `docker_socket_unit_path` | `/lib/systemd/system/docker.socket` | docker.socket unit 경로 | `ls -l /usr/lib/systemd/system/docker.socket /lib/systemd/system/docker.socket` | `group_vars/docker.yml` | 중간 | socket activation 사용 여부 확인 |
| Docker | `docker_config_dir` | `/etc/docker` | Docker 설정 디렉터리 | `ls -ld /etc/docker` | 기본값 또는 `group_vars/docker.yml` | 중간 | 권한 변경 대상 |
| Docker | `docker_socket_path` | `/var/run/docker.sock` | Docker API socket | `ls -l /var/run/docker.sock` | 기본값 또는 `group_vars/docker.yml` | 높음 | 잘못되면 권한 task 누락 |
| Docker | `docker_daemon_config_path` | `/etc/docker/daemon.json` | daemon.json 경로 | `ls -l /etc/docker/daemon.json` | 기본값 또는 `group_vars/docker.yml` | 높음 | daemon 설정 병합 시 중요 |
| Docker | `docker_apply_audit_config` | `false` | audit rule 적용 여부 | `systemctl status auditd`, `auditctl -l` | `group_vars/docker.yml` | 높음 | 기본 비활성 유지 |
| Docker | `audit_rules_file` | `/etc/audit/rules.d/audit.rules` | audit rules 파일 | `ls -l /etc/audit/rules.d/audit.rules` | `group_vars/docker.yml` | 중간 | OS별 파일명 정책 확인 |
| Docker | `docker_audit_watch_paths` | Docker 주요 경로 목록 | audit watch 대상 경로 존재 여부 | `ls -l /usr/bin/docker /var/lib/docker /etc/docker` | `group_vars/docker.yml` | 중간 | 없는 경로는 skip |
| Docker | `docker_runtime_check_mode` | `warn` | runtime 점검 결과 처리 방식 | `docker ps`, 운영 정책 검토 | 기본값 권장 | 낮음 | fail 전환 시 pipeline 실패 가능 |
| Docker | `docker_enable_runtime_container_checks` | `true` | 컨테이너 런타임 점검 여부 | `docker ps`, `docker inspect <container>` | 기본값 권장 | 낮음 | report 중심 |
| Docker | `docker_apply_package_update` | `false` | Docker 패키지 업데이트 여부 | 패치 윈도우 확인 | `group_vars/docker.yml` | 매우 높음 | 기본 비활성 유지 |
| Docker | `docker_restart_service` | `false` | Docker 서비스 재시작 여부 | 컨테이너 영향 검토 | `group_vars/docker.yml` | 매우 높음 | 기본 비활성 유지 |
| Docker | `docker_apply_daemon_security`, `docker_enable_daemon_config_extension`, `docker_daemon_config` | `false`, `false`, `{}` | daemon.json 보안 옵션 병합 여부/내용 | `docker info`, `cat /etc/docker/daemon.json` | `group_vars/docker.yml` | 매우 높음 | Docker 재시작과 런타임 영향 |

### Kubernetes

| 영역 | 변수명 | 현재 기본값 | 실제 운영환경에서 확인해야 하는 값 | 확인 방법/명령어 | 어디에 넣을지 | 위험도 | 비고 |
| -- | --- | ------ | ------------------- | --------- | ------- | --- | -- |
| Kubernetes | `k8s_node_role` | `auto` | 노드 역할 | `kubectl --kubeconfig /etc/kubernetes/admin.conf get nodes -o wide` | 기본값 또는 host별 | 중간 | 보통 auto 유지 |
| Kubernetes | `k8s_manifest_dir` | `/etc/kubernetes/manifests` | static pod manifest 디렉터리 | `ls -l /etc/kubernetes/manifests` | `group_vars/k8s.yml` | 매우 높음 | control-plane 변경 대상 |
| Kubernetes | `k8s_apiserver_manifest` | `{{ k8s_manifest_dir }}/kube-apiserver.yaml` | kube-apiserver manifest | `ls -l /etc/kubernetes/manifests/kube-apiserver.yaml` | 기본값 또는 `group_vars/k8s.yml` | 매우 높음 | 수정 시 control-plane 영향 |
| Kubernetes | `k8s_etcd_manifest` | `{{ k8s_manifest_dir }}/etcd.yaml` | etcd manifest | `ls -l /etc/kubernetes/manifests/etcd.yaml` | 기본값 또는 `group_vars/k8s.yml` | 매우 높음 | control-plane 영향 |
| Kubernetes | `k8s_pki_dir` | `/etc/kubernetes/pki` | Kubernetes PKI 디렉터리 | `ls -l /etc/kubernetes/pki` | `group_vars/k8s.yml` | 높음 | TLS args에 사용 |
| Kubernetes | `k8s_etcd_pki_dir` | `/etc/kubernetes/pki/etcd` | etcd PKI 디렉터리 | `ls -l /etc/kubernetes/pki/etcd` | `group_vars/k8s.yml` | 매우 높음 | etcd TLS 적용 시 필수 |
| Kubernetes | `k8s_etcd_data_dir` | `/var/lib/etcd` | etcd data dir | `ls -ld /var/lib/etcd` | `group_vars/k8s.yml` | 매우 높음 | 권한 변경 전 snapshot 필수 |
| Kubernetes | `k8s_kubelet_config_file` | `/var/lib/kubelet/config.yaml` | kubelet config | `ls -l /var/lib/kubelet/config.yaml` | `group_vars/k8s.yml` | 높음 | kubelet 설정 변경 대상 |
| Kubernetes | `k8s_kubectl_config` | `/etc/kubernetes/admin.conf` | kubectl kubeconfig | `ls -l /etc/kubernetes/admin.conf` | `group_vars/k8s.yml` | 중간 | 점검 command에 사용 |
| Kubernetes | `k8s_audit_policy_file`, `k8s_audit_log_path` | `/etc/kubernetes/audit-policy.yaml`, `/var/log/kubernetes/audit/audit.log` | audit policy/log 경로 | `ls -l /etc/kubernetes/audit-policy.yaml`, `ls -ld /var/log/kubernetes/audit` | `group_vars/k8s.yml` | 높음 | audit 활성화 시 사용 |
| Kubernetes | `k8s_psa_namespace` | `default` | PSA 적용 대상 namespace | `kubectl --kubeconfig /etc/kubernetes/admin.conf get ns --show-labels` | `group_vars/k8s.yml` | 높음 | workload 차단 가능 |
| Kubernetes | `k8s_network_policy_namespace` | `{{ k8s_psa_namespace }}` | NetworkPolicy 대상 namespace | `kubectl --kubeconfig /etc/kubernetes/admin.conf get networkpolicy -A` | `group_vars/k8s.yml` | 매우 높음 | default deny 영향 |
| Kubernetes | `k8s_rbac_namespace`, `k8s_secret_namespace` | `{{ k8s_psa_namespace }}` | RBAC/Secret 정책 대상 namespace | `kubectl --kubeconfig /etc/kubernetes/admin.conf get ns` | `group_vars/k8s.yml` | 높음 | 대상 workload 확인 |
| Kubernetes | `k8s_apply_control_plane`, `k8s_apply_api_server` | `false`, `false` | static pod manifest 수정 여부 | manifest 백업, control-plane 점검 | `group_vars/k8s.yml` | 매우 높음 | 기본 비활성 유지 |
| Kubernetes | `k8s_apply_etcd_tls`, `k8s_apply_etcd_encryption_config`, `k8s_apply_etcd_permissions` | `false` | etcd TLS/Secret 암호화/권한 적용 여부 | etcd snapshot, cert 7개 확인 | `group_vars/k8s.yml` | 매우 높음 | Secret 재암호화 절차 필요 |
| Kubernetes | `k8s_encryption_config_secret` | `""` | Secret encryption key | 별도 보안 채널에서 생성/보관 | vault 또는 host_vars | 매우 높음 | 평문 커밋 금지 |
| Kubernetes | `k8s_apply_kubelet`, `k8s_restart_kubelet` | `false`, `false` | kubelet 설정 변경/재시작 여부 | node drain 필요성 검토 | `group_vars/k8s.yml` | 매우 높음 | workload 영향 |
| Kubernetes | `k8s_apply_policies`, `k8s_apply_psa_labels`, `k8s_enable_network_policies`, `k8s_enable_rbac_controls`, `k8s_enable_secret_controls` | `false` | PSA/RBAC/NetworkPolicy/Secret 정책 적용 여부 | namespace/workload 영향 검토 | `group_vars/k8s.yml` | 매우 높음 | 기본 check/report 중심 |
| Kubernetes | `k8s_check_policies`, `k8s_enable_pod_security_checks`, `k8s_fail_on_policy_violation` | `true`, `true`, `false` | 점검/report 강도 | `kubectl get pods -A -o yaml` | 기본값 권장 | 낮음 | fail 전환 전 CI 영향 확인 |

## 3. 실제 서버에서 확인할 명령어 모음

### DB

```bash
mysql -e "SELECT @@VERSION, @@VERSION_COMMENT;"
mysql -e "SELECT User, Host FROM mysql.user ORDER BY User, Host;"
mysqladmin variables | grep socket
ss -xl | grep mysql
systemctl list-units '*mariadb*' '*mysql*'
ps -eo user,comm,args | grep -E 'mysqld|mariadbd'
ls -l /etc/my.cnf /etc/mysql/my.cnf /etc/mysql/mariadb.conf.d/50-server.cnf
ls -ld /var/log/mysql
df -h /var/log
```

### OpenStack

```bash
ls -l /etc/keystone/keystone.conf
ls -l /etc/nova/nova.conf
ls -l /etc/cinder/cinder.conf
ls -l /etc/glance/glance-api.conf
ls -l /etc/neutron/neutron.conf
openstack endpoint list
systemctl status apache2 nova-api cinder-api glance-api neutron-server
ls -l /root/admin-openrc
. /root/admin-openrc && openstack token issue
openssl s_client -connect <keystone-host>:5000 -showcerts </dev/null
```

### Docker

```bash
getent group docker
ls -l /usr/lib/systemd/system/docker.service
ls -l /lib/systemd/system/docker.service
ls -l /usr/lib/systemd/system/docker.socket
ls -l /lib/systemd/system/docker.socket
ls -l /var/run/docker.sock
ls -ld /etc/docker
ls -l /etc/docker/daemon.json
systemctl status docker
systemctl status auditd
auditctl -l
docker ps
docker inspect <container>
docker info
```

### Kubernetes

```bash
ls -l /etc/kubernetes/manifests
ls -l /etc/kubernetes/manifests/kube-apiserver.yaml
ls -l /etc/kubernetes/manifests/etcd.yaml
ls -l /etc/kubernetes/pki
ls -l /etc/kubernetes/pki/etcd
ls -ld /var/lib/etcd
ls -l /var/lib/kubelet/config.yaml
ls -l /etc/kubernetes/admin.conf
kubectl --kubeconfig /etc/kubernetes/admin.conf get nodes -o wide
kubectl --kubeconfig /etc/kubernetes/admin.conf get ns --show-labels
kubectl --kubeconfig /etc/kubernetes/admin.conf get networkpolicy -A
kubectl --kubeconfig /etc/kubernetes/admin.conf get pods -A -o wide
```

## 4. group_vars/host_vars 작성 예시

아래 예시는 운영 값의 위치와 형태를 보여주기 위한 것입니다. 그대로 복사해 쓰기 전에 반드시 실제 서버에서 확인하세요.

```yaml
# group_vars/db.yml
db_config_file: /etc/mysql/mariadb.conf.d/50-server.cnf
db_login_unix_socket: /var/run/mysqld/mysqld.sock
db_service_name: mariadb
db_runtime_user: mysql
db_runtime_group: mysql

db_account_delete_protected_users_extra:
  - keystone
  - nova
  - cinder
  - glance
  - neutron
  - backup
  - dba_admin
  - replication

db_privilege_exempt_users:
  - prometheus
  - mysqld_exporter
  - dba_admin

db_regular_users:
  - name: app_readonly
    host: "%"

db_unnecessary_accounts:
  - name: old_test_user
    host: "%"

db_disallowed_account_hosts:
  - name: app_readonly
    host: "0.0.0.0"

db_apply_password_policy: false
db_apply_security_patch: false
```

```yaml
# group_vars/openstack_controllers.yml
keystone_security_config_file: /etc/keystone/keystone.conf
keystone_security_service_name: apache2
keystone_security_openrc_path: /root/admin-openrc
keystone_security_enable_tls: false
keystone_security_restart_service: false

nova_security_config_file: /etc/nova/nova.conf
nova_security_service_name: nova-api
nova_security_enable_tls: false
nova_security_restart_service: false

cinder_security_config_file: /etc/cinder/cinder.conf
cinder_security_service_name: cinder-api
cinder_security_enable_tls: false
cinder_security_restart_service: false

glance_security_config_file: /etc/glance/glance-api.conf
glance_security_service_name: glance-api
glance_security_enable_tls: false
glance_security_restart_service: false

neutron_security_config_file: /etc/neutron/neutron.conf
neutron_security_service_name: neutron-server
neutron_security_enable_tls: false
neutron_security_restart_service: false
```

```yaml
# group_vars/openstack_tls.yml
# TLS 전환 승인 후에만 사용합니다.
keystone_security_enable_tls: true
keystone_security_tls_endpoint_change_confirmed: true
keystone_security_public_endpoint: https://keystone.example.com:5000
keystone_security_certfile: /etc/keystone/ssl/certs/keystone.pem
keystone_security_keyfile: /etc/keystone/ssl/private/keystonekey.pem
keystone_security_cafile: /etc/keystone/ssl/certs/ca.pem
keystone_security_ca_cert: /etc/ssl/certs/openstack-ca.pem

nova_security_enable_tls: true
nova_security_keystone_tls_confirmed: true
nova_security_keystone_endpoint: https://keystone.example.com:5000/v3
nova_security_glance_endpoint: https://glance.example.com:9292
nova_security_ca_cert: /etc/ssl/certs/openstack-ca.pem

cinder_security_enable_tls: true
cinder_security_keystone_tls_confirmed: true
cinder_security_keystone_endpoint: https://keystone.example.com:5000/v3
cinder_security_nova_endpoint: https://nova.example.com:8774/v2.1
cinder_security_glance_endpoint: https://glance.example.com:9292
cinder_security_ca_cert: /etc/ssl/certs/openstack-ca.pem

glance_security_enable_tls: true
glance_security_keystone_tls_confirmed: true
glance_security_keystone_endpoint: https://keystone.example.com:5000/v3
glance_security_ca_cert: /etc/ssl/certs/openstack-ca.pem

neutron_security_enable_tls: true
neutron_security_keystone_tls_confirmed: true
neutron_security_keystone_endpoint: https://keystone.example.com:5000/v3
neutron_security_api_endpoint: https://neutron.example.com:9696
neutron_security_ca_cert: /etc/ssl/certs/openstack-ca.pem
```

```yaml
# group_vars/docker.yml
docker_group_name: docker
docker_allowed_users:
  - root
  - ansible
docker_disallowed_group_users: []

docker_service_unit_path: /lib/systemd/system/docker.service
docker_socket_unit_path: /lib/systemd/system/docker.socket
docker_config_dir: /etc/docker
docker_daemon_config_path: /etc/docker/daemon.json
docker_socket_path: /var/run/docker.sock

docker_runtime_check_mode: warn
docker_apply_package_update: false
docker_apply_audit_config: false
docker_apply_daemon_security: false
docker_enable_daemon_config_extension: false
docker_restart_service: false
```

```yaml
# group_vars/k8s.yml
k8s_node_role: auto
k8s_kubectl_config: /etc/kubernetes/admin.conf
k8s_manifest_dir: /etc/kubernetes/manifests
k8s_pki_dir: /etc/kubernetes/pki
k8s_etcd_pki_dir: /etc/kubernetes/pki/etcd
k8s_etcd_data_dir: /var/lib/etcd
k8s_kubelet_config_file: /var/lib/kubelet/config.yaml

k8s_check_policies: true
k8s_enable_pod_security_checks: true
k8s_fail_on_policy_violation: false

k8s_psa_namespace: default
k8s_network_policy_namespace: default
k8s_rbac_namespace: default
k8s_secret_namespace: default

k8s_apply_control_plane: false
k8s_apply_api_server: false
k8s_apply_etcd_tls: false
k8s_apply_etcd_encryption_config: false
k8s_apply_kubelet: false
k8s_apply_policies: false
k8s_restart_kubelet: false
```
