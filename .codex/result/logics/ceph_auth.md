# ceph_auth

## 기능 한줄정리

CephX 인증 설정을 조회하고, 명시 승인된 경우 cluster/service/client 인증 요구값과 client keyring을 적용합니다.

## 적용방법

1. 기본값은 `enable_cephx_enforcement: false`, `ceph_auth_report_only: true`입니다.
2. 인증 설정 변경은 `enable_cephx_enforcement: true`, `ceph_auth_report_only: false`, `security_action_mode: enforce`가 모두 필요합니다.
3. client keyring 배포는 `ceph_deploy_keyrings: true`와 `ceph_clients[].keyring_content`가 필요합니다.

## 제공인자

| 인자 | 기본값 | 설명 |
|---|---:|---|
| `enable_cephx_enforcement` | `false` | CephX 강제 적용 여부 |
| `ceph_auth_cluster_required` | `cephx` | cluster 인증 요구값 |
| `ceph_auth_service_required` | `cephx` | service 인증 요구값 |
| `ceph_auth_client_required` | `cephx` | client 인증 요구값 |
| `ceph_deploy_keyrings` | `false` | client keyring 배포 여부 |
| `ceph_auth_report_only` | `true` | 점검 전용 여부 |
| `ceph_clients` | `[]` | client keyring 배포 정책 |

## 세부 진행단계

1. `ceph config get mon auth_*_required`로 현재 인증 설정을 조회합니다.
2. 현재값과 목표값을 report로 출력합니다.
3. enforce + CephX enable + report_only false 조건에서 `ceph config set mon`을 실행합니다.
4. `ceph_deploy_keyrings`가 true이면 `ceph_clients` 목록을 순회합니다.
5. `keyring`과 `keyring_content`가 정의된 client만 keyring 파일을 배포합니다.
6. keyring owner/group/mode는 client 항목 또는 기본 서비스 keyring mode를 사용합니다.

## 단일기능 실행방법

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags ceph_auth \
  --limit ceph_hosts \
  --check --diff
```

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags ceph_auth \
  --limit ceph_hosts \
  -e "enable_cephx_enforcement=true ceph_auth_report_only=false security_action_mode=enforce"
```
