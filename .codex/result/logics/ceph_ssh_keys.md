# ceph_ssh_keys

## 기능 한줄정리

Ceph 관리 계정의 `.ssh` 디렉터리와 private key 권한을 점검/보정하고, 선택적으로 authorized_keys를 관리합니다.

## 적용방법

1. 기본 report로 대상 사용자 홈 디렉터리와 key 관리 정책을 확인합니다.
2. 실제 권한 보정은 `security_action_mode: enforce`에서 수행합니다.
3. `authorized_keys` 내용 관리는 `ceph_manage_authorized_keys: true`와 사용자별 정책이 있을 때만 수행합니다.

## 제공인자

| 인자 | 기본값 | 설명 |
|---|---:|---|
| `enable_ceph_ssh_key_check` | `true` | 기능 활성화 여부 |
| `ceph_ssh_users` | `root`, `ceph`, `ansible` | 점검 대상 사용자 |
| `ceph_ssh_dir_mode` | `0700` | `.ssh` 디렉터리 권한 |
| `ceph_private_key_mode` | `0600` | private key 권한 |
| `ceph_authorized_keys_mode` | `0600` | authorized_keys 권한 |
| `ceph_manage_authorized_keys` | `false` | authorized_keys 관리 여부 |
| `ceph_purge_unmanaged_keys` | `false` | 미승인 키 제거 정책값 |
| `ceph_authorized_keys_policy` | `{}` | 사용자별 authorized_keys 목록 |

## 세부 진행단계

1. `getent passwd`로 대상 사용자 존재 여부와 홈 디렉터리를 조회합니다.
2. 조회된 사용자 홈 정보를 fact로 구성합니다.
3. 대상 사용자, 홈, authorized_keys 관리 여부를 report로 출력합니다.
4. enforce 모드에서 `.ssh` 디렉터리를 생성하고 권한을 적용합니다.
5. enforce 모드에서 `id_*` private key 파일을 찾아 권한을 보정합니다.
6. `ceph_manage_authorized_keys`가 true이고 정책이 있는 사용자에 대해 authorized_keys 파일을 배포합니다.

## 단일기능 실행방법

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags ceph_ssh_keys \
  --limit ceph_hosts \
  --check --diff
```

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags ceph_ssh_keys \
  --limit ceph_hosts \
  -e "security_action_mode=enforce"
```
