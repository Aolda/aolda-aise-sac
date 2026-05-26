# k8s-security

Kubernetes Control Plane, API Server, etcd, Kubelet, Pod Security Admission 설정을 강화하고 기존 Pod 보안 상태를 점검하는 Ansible Role입니다.

## 구현 task

| 파일 | 구현 내용 |
| --- | --- |
| `tasks/1_control_plane.yml` | Controller Manager 인증/TLS 파라미터를 추가하고, master 주요 설정 파일과 인증서/키 파일, etcd 데이터 디렉터리 권한을 제한하며 Kubernetes 버전을 출력합니다. |
| `tasks/2_api_server.yml` | API Server 익명 인증 차단, RBAC/Node 인가, 취약한 token auth 제거, Scheduler/Controller Manager bind address 제한, Admission Plugin, TLS, Audit Log 설정을 적용합니다. |
| `tasks/3_etcd.yml` | API Server의 etcd 저장 데이터 암호화 설정, API Server와 etcd 간 TLS 인증서 설정, etcd 서버 TLS/클라이언트 인증 설정, etcd 데이터 디렉터리 권한을 적용합니다. |
| `tasks/4_kubelet.yml` | Kubelet 익명 인증 차단, Webhook 인가, kernel 기본값 보호, TLS cipher suite, kubelet 설정/인증서 파일 권한을 적용하고 kubelet 버전을 출력합니다. |
| `tasks/5_policies.yml` | 대상 네임스페이스에 Pod Security Admission 라벨을 적용하고, RBAC/NetworkPolicy/Secret 관리 정책과 안전한 Pod 예시 템플릿을 조건부로 배포합니다. |
| `tasks/6_pod_security_checks.yml` | 기존 Pod의 host namespace 공유, 컨테이너 `securityContext`, RBAC/NetworkPolicy/Secret 관련 상태를 점검합니다. |

## 적용이 필요한 이유

- API Server와 Kubelet의 익명 접근 또는 약한 인가는 클러스터 전체 권한 노출로 이어질 수 있습니다.
- Control Plane 컴포넌트를 외부 인터페이스에 노출하면 관리 API 공격면이 넓어집니다.
- 인증서, key, kubeconfig, etcd 데이터 권한은 클러스터 관리자 권한과 직접 연결됩니다.
- etcd 암호화와 TLS는 Secret 등 민감 데이터의 저장/전송 보호에 필요합니다.
- PSA Restricted 정책은 권한 상승 컨테이너, host namespace 공유, 과도한 Linux capability 사용을 줄입니다.
- 기존 Pod 점검은 PSA 적용 전후에 이미 떠 있는 워크로드의 보안 설정 누락을 찾는 데 필요합니다.

## 적용 시 변경점

- `/etc/kubernetes/manifests` 하위 정적 파드 manifest에 보안 파라미터가 추가 또는 갱신됩니다.
- 취약한 `--token-auth-file` 설정이 제거됩니다.
- 주요 kubeconfig/manifest 파일은 `root:root`, `0644`로 조정됩니다.
- 인증서 파일은 `0644`, key 파일은 `0600`, etcd 데이터 디렉터리는 `0700`으로 조정됩니다.
- 선택 변수 활성화 시 API Server audit log와 encryption provider config 경로가 설정되며, 관리 옵션을 켜면 관련 설정 파일도 생성됩니다.
- `/var/lib/kubelet/config.yaml`의 인증/인가/TLS/kernel 보호 설정이 변경됩니다.
- PSA 라벨이 네임스페이스에 적용되고 `/etc/kubernetes/secure-pod-template.yaml`이 생성됩니다.
- `k8s_enable_rbac_controls`가 `true`이면 제한된 ServiceAccount, Role, RoleBinding이 생성됩니다.
- `k8s_enable_network_policies`가 `true`이면 default deny NetworkPolicy와 DNS egress 허용 정책이 생성됩니다. 앱 통신 차단 위험이 있어 기본값은 `false`입니다.
- `k8s_disable_default_service_account_token_automount`가 `true`이면 default ServiceAccount의 API 토큰 자동 마운트를 비활성화합니다. Kubernetes API를 호출하는 Pod에 영향이 있어 기본값은 `false`입니다.
- `k8s_enable_pod_security_checks`가 `true`이면 기존 Pod 보안 설정을 점검합니다. 기본값은 경고 출력이며, `k8s_fail_on_policy_violation`을 `true`로 설정하면 위반을 실패 처리합니다.
- manifest 변경 시 Kubelet 서비스가 재시작되어 정적 파드 재기동을 유도합니다.

## 변수 설명

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `k8s_kubelet_service_name` | `kubelet` | 재시작할 Kubelet 서비스명입니다. |
| `k8s_apply_control_plane` | `true` | Control Plane task 적용 여부입니다. |
| `k8s_apply_api_server` | `true` | API Server task 적용 여부입니다. |
| `k8s_apply_etcd` | `true` | etcd task 적용 여부입니다. |
| `k8s_apply_kubelet` | `true` | Kubelet task 적용 여부입니다. |
| `k8s_apply_policies` | `true` | PSA/Pod template task 적용 여부입니다. |
| `k8s_manifest_dir` | `/etc/kubernetes/manifests` | 정적 파드 manifest 디렉터리입니다. |
| `k8s_pki_dir` | `/etc/kubernetes/pki` | Kubernetes 인증서 디렉터리입니다. |
| `k8s_etcd_pki_dir` | `/etc/kubernetes/pki/etcd` | etcd 인증서 디렉터리입니다. |
| `k8s_etcd_data_dir` | `/var/lib/etcd` | etcd 데이터 디렉터리입니다. |
| `k8s_apiserver_manifest` 외 manifest 변수 | `k8s_manifest_dir` 기반 | API Server, Controller Manager, Scheduler, etcd manifest 경로입니다. |
| `k8s_master_config_files` | 목록 | 권한을 `0644`로 제한할 master 설정 파일 목록입니다. |
| `k8s_controller_manager_args` | 목록 | Controller Manager에 적용할 인증/TLS/인증서 rotation 인자입니다. |
| `k8s_scheduler_bind_address` | `127.0.0.1` | Scheduler bind address입니다. |
| `k8s_controller_manager_bind_address` | `127.0.0.1` | Controller Manager bind address입니다. |
| `k8s_apiserver_auth_args` | 목록 | API Server 인증/인가 인자입니다. |
| `k8s_apiserver_enable_admission_plugins` | `NodeRestriction,...` | 활성화할 Admission Plugin 목록입니다. |
| `k8s_apiserver_disable_admission_plugins` | `NamespaceLifecycle,AlwaysAdmin` | 비활성화할 Admission Plugin 목록입니다. |
| `k8s_admission_control_config_file` | `/etc/kubernetes/admission-control-config.yaml` | Admission Control Config 파일 경로입니다. |
| `k8s_enable_admission_control_config` | `false` | Admission Control Config 인자 적용 여부입니다. |
| `k8s_apiserver_tls_args` | 목록 | API Server TLS 인증서 및 cipher suite 인자입니다. |
| `k8s_audit_policy_file` | `/etc/kubernetes/audit-policy.yaml` | Audit Policy 파일 경로입니다. |
| `k8s_audit_log_path` | `/var/log/kubernetes/audit/audit.log` | API Server 감사 로그 경로입니다. |
| `k8s_audit_log_dir` | `k8s_audit_log_path`의 디렉터리 | 감사 로그 디렉터리 경로입니다. |
| `k8s_audit_log_maxage` | `30` | 감사 로그 보관 일수입니다. |
| `k8s_audit_log_maxbackup` | `10` | 감사 로그 백업 파일 개수입니다. |
| `k8s_audit_log_maxsize` | `100` | 감사 로그 파일 최대 크기(MB)입니다. |
| `k8s_enable_audit_log` | `false` | API Server Audit Log 인자 적용 여부입니다. |
| `k8s_manage_audit_policy_file` | `false` | Audit Policy 파일을 role에서 생성할지 여부입니다. |
| `k8s_audit_policy_content` | Metadata audit policy | 생성할 Audit Policy 파일 내용입니다. |
| `k8s_encryption_provider_config` | `/etc/kubernetes/encryption-config.yaml` | etcd 저장 데이터 암호화 설정 파일 경로입니다. |
| `k8s_enable_encryption_provider_config` | `false` | encryption provider config 인자 적용 여부입니다. |
| `k8s_manage_encryption_config_file` | `false` | EncryptionConfiguration 파일을 role에서 생성할지 여부입니다. |
| `k8s_encryption_config_secret` | `""` | EncryptionConfiguration 생성 시 사용할 base64 인코딩된 암호화 키입니다. |
| `k8s_encryption_config_content` | Secret aescbc 설정 | 생성할 EncryptionConfiguration 파일 내용입니다. |
| `k8s_apiserver_etcd_tls_args` | 목록 | API Server가 etcd 접속에 사용할 TLS 인자입니다. |
| `k8s_etcd_server_args` | 목록 | etcd 서버 TLS 및 클라이언트 인증 인자입니다. |
| `k8s_kubelet_config_file` | `/var/lib/kubelet/config.yaml` | Kubelet config 파일 경로입니다. |
| `k8s_kubelet_pki_dir` | `/var/lib/kubelet/pki` | Kubelet 인증서 디렉터리입니다. |
| `k8s_kubelet_config_files` | 목록 | 권한을 제한할 Kubelet 관련 설정 파일 목록입니다. |
| `k8s_kubelet_tls_cipher_suites` | 목록 | Kubelet에 적용할 TLS cipher suite 목록입니다. |
| `k8s_psa_namespace` | `default` | PSA 라벨을 적용할 네임스페이스입니다. |
| `k8s_psa_enforce_level` | `restricted` | PSA enforce level입니다. |
| `k8s_psa_warn_level` | `restricted` | PSA warn level입니다. |
| `k8s_secure_pod_template_path` | `/etc/kubernetes/secure-pod-template.yaml` | 안전한 Pod 예시 템플릿 배포 경로입니다. |
| `k8s_enable_pod_security_checks` | `true` | 기존 Pod 보안 설정 점검 실행 여부입니다. |
| `k8s_fail_on_policy_violation` | `false` | Pod 보안 정책 위반을 role 실패로 처리할지 여부입니다. |
| `k8s_enable_rbac_controls` | `true` | 제한된 ServiceAccount/Role/RoleBinding 생성 여부입니다. |
| `k8s_rbac_namespace` | `k8s_psa_namespace` | RBAC 정책을 적용할 네임스페이스입니다. |
| `k8s_restricted_service_account` | `restricted-workload` | 제한된 워크로드용 ServiceAccount 이름입니다. |
| `k8s_restricted_role_name` | `restricted-readonly` | 최소 권한 Role 이름입니다. |
| `k8s_restricted_role_rules` | 목록 | 최소 권한 Role에 부여할 규칙입니다. |
| `k8s_enable_network_policies` | `false` | default deny NetworkPolicy 적용 여부입니다. 앱 통신 차단 위험이 있어 기본 비활성입니다. |
| `k8s_network_policy_namespace` | `k8s_psa_namespace` | NetworkPolicy를 적용할 네임스페이스입니다. |
| `k8s_default_deny_network_policy_name` | `default-deny-all` | default deny NetworkPolicy 이름입니다. |
| `k8s_allow_dns_network_policy_name` | `allow-dns-egress` | DNS egress 허용 NetworkPolicy 이름입니다. |
| `k8s_enable_dns_egress_policy` | `true` | NetworkPolicy 적용 시 DNS egress 허용 정책도 함께 적용할지 여부입니다. |
| `k8s_enable_secret_controls` | `true` | Secret 관련 템플릿/점검 실행 여부입니다. |
| `k8s_secret_namespace` | `k8s_psa_namespace` | Secret 관련 제어 대상 네임스페이스입니다. |
| `k8s_secret_template_path` | `/etc/kubernetes/secure-secret-template.yaml` | 안전한 Secret 예시 템플릿 배포 경로입니다. |
| `k8s_disable_default_service_account_token_automount` | `false` | default ServiceAccount 토큰 자동 마운트 비활성화 여부입니다. API 사용 Pod 영향이 있어 기본 비활성입니다. |
