# ceph_selinux

## 기능 한줄정리

Ubuntu 24.04 Ceph 노드에서 SELinux 상태와 AVC 로그를 보고하고, 명시된 경우 SELinux 패키지/상태 변경을 수행합니다.

## 적용방법

1. Ubuntu 기본 운영 모델을 고려해 `enable_ceph_selinux: false`가 기본입니다.
2. 상태/AVC report는 `ceph_selinux_report_avc: true`로 수행합니다.
3. 실제 패키지 설치나 `setenforce` 실행은 `enable_ceph_selinux: true`, `security_action_mode: enforce`가 필요합니다.
4. 재부팅은 `ceph_selinux_allow_reboot: true`일 때만 수행합니다.

## 제공인자

| 인자 | 기본값 | 설명 |
|---|---:|---|
| `enable_ceph_selinux` | `false` | SELinux 적용 여부 |
| `ceph_selinux_state` | `permissive` | 목표 상태 |
| `ceph_selinux_policy` | `targeted` | SELinux policy 값 |
| `ceph_selinux_install_packages` | `false` | 관련 패키지 설치 여부 |
| `ceph_selinux_allow_reboot` | `false` | 재부팅 허용 여부 |
| `ceph_selinux_report_avc` | `true` | AVC 로그 report 여부 |

## 세부 진행단계

1. `sestatus`로 SELinux 상태를 조회합니다.
2. `ausearch -m avc -ts recent`로 최근 AVC 로그를 조회합니다.
3. SELinux 활성화 여부, 목표 상태, 재부팅 허용 여부를 report로 출력합니다.
4. enforce + 패키지 설치 true 조건에서 SELinux 관련 패키지를 설치합니다.
5. enforce + 상태가 permissive/enforcing이면 `setenforce`를 실행합니다.
6. 재부팅 허용 조건이 true이면 reboot를 수행합니다.

## 단일기능 실행방법

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags ceph_selinux \
  --limit ceph_hosts \
  --check --diff
```

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags ceph_selinux \
  --limit ceph_hosts \
  -e "enable_ceph_selinux=true security_action_mode=enforce ceph_selinux_state=permissive"
```
