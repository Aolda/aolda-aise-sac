# ceph_config

## 기능 한줄정리

Ceph 설정 파일의 민감정보 포함 여부를 탐지하고, 일반/민감 설정에 맞는 권한을 적용합니다.

## 적용방법

1. 기본 report로 설정 파일 존재 여부와 민감정보 탐지 결과를 확인합니다.
2. 실제 권한 적용은 `security_action_mode: enforce`에서 수행합니다.
3. 민감정보 판단 기준은 `ceph_config_secret_patterns`로 조정합니다.

## 제공인자

| 인자 | 기본값 | 설명 |
|---|---:|---|
| `enable_ceph_config_permission_check` | `true` | 기능 활성화 여부 |
| `ceph_config_files` | `/etc/ceph/ceph.conf` | 점검 대상 설정 파일 |
| `ceph_config_default_mode` | `0644` | 일반 설정 권한 |
| `ceph_config_secret_mode` | `0640` | 민감정보 포함 시 권한 |
| `ceph_config_owner` | `root` | 파일 소유자 |
| `ceph_config_group` | `ceph` | 파일 그룹 |
| `ceph_config_secret_patterns` | `key`, `secret`, `password` | 민감정보 탐지 패턴 |

## 세부 진행단계

1. `ceph_config_files` 목록의 파일 stat 정보를 조회합니다.
2. 각 파일에 대해 민감정보 패턴을 grep으로 검사합니다.
3. 파일이 없으면 `absent`, 민감정보가 있으면 `secret`, 없으면 `normal`로 분류합니다.
4. 분류 결과와 정책값을 report로 출력합니다.
5. enforce 모드에서 존재하는 파일에 owner/group/mode를 적용합니다.
6. `secret` 파일은 `ceph_config_secret_mode`, `normal` 파일은 `ceph_config_default_mode`를 사용합니다.

## 단일기능 실행방법

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags ceph_config \
  --limit ceph_hosts \
  --check --diff
```

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags ceph_config \
  --limit ceph_hosts \
  -e "security_action_mode=enforce"
```
