# ceph_admin_user

## 기능 한줄정리

Ceph 운영용 관리자 계정과 sudoers 정책을 관리하고, 선택적으로 root SSH 접속을 제한합니다.

## 적용방법

1. 기본 report로 관리자 계정/그룹/sudo 정책을 확인합니다.
2. 실제 계정/그룹/sudoers 생성은 `security_action_mode: enforce`에서 수행합니다.
3. root SSH 차단은 `ceph_disable_root_ssh: true`일 때만 적용됩니다.

## 제공인자

| 인자 | 기본값 | 설명 |
|---|---:|---|
| `enable_ceph_admin_user_policy` | `true` | 기능 활성화 여부 |
| `ceph_admin_users` | `cephadmin`, `ansible` | Ceph 관리자 계정 |
| `ceph_admin_groups` | `sudo` | 관리자 그룹 |
| `ceph_admin_sudo_nopasswd` | `true` | passwordless sudo 여부 |
| `ceph_admin_sudo_commands` | `ALL` | 허용 sudo 명령 |
| `ceph_disable_root_ssh` | `false` | root SSH 차단 여부 |
| `ceph_admin_sudoers_path` | `/etc/sudoers.d/90-ceph-admin-users` | sudoers 파일 경로 |

## 세부 진행단계

1. 관리자 계정, 그룹, sudo 정책, root SSH 제한 여부를 report로 출력합니다.
2. enforce 모드에서 관리자 그룹을 생성합니다.
3. enforce 모드에서 관리자 계정을 생성하고 그룹에 추가합니다.
4. sudoers 템플릿을 렌더링합니다.
5. 렌더링 결과를 `visudo -cf`로 검증한 뒤 배포합니다.
6. `ceph_disable_root_ssh`가 true이면 SSH drop-in으로 `PermitRootLogin no`를 배포합니다.
7. SSH 설정이 변경되면 `ssh` 서비스를 reload합니다.

## 단일기능 실행방법

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags ceph_admin_user \
  --limit ceph_hosts \
  --check --diff
```

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags ceph_admin_user \
  --limit ceph_hosts \
  -e "security_action_mode=enforce"
```
