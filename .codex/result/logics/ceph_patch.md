# ceph_patch

## 기능 한줄정리

Ceph 클러스터 health와 패키지 후보 버전을 확인하고, health 기준 충족 시 명시 모드에서 Ceph 패치를 수행합니다.

## 적용방법

1. 기본 `ceph_patch_mode: report`로 health와 패키지 후보 버전을 확인합니다.
2. 실제 패치는 `enable_ceph_patch: true`, `security_action_mode: enforce`, 비-report 패치 모드가 필요합니다.
3. 패치 전 `ceph_patch_health_required` 기준을 만족해야 합니다.
4. 재부팅은 `ceph_allow_reboot: true`일 때만 수행합니다.

## 제공인자

| 인자 | 기본값 | 설명 |
|---|---:|---|
| `enable_ceph_patch` | `false` | 패치 활성화 여부 |
| `ceph_patch_mode` | `report` | `report`, `security_only`, `point_release`, `specific_version` |
| `ceph_target_version` | `""` | 특정 목표 버전 |
| `ceph_patch_health_required` | `HEALTH_OK` | 패치 전 요구 health |
| `ceph_rolling_patch` | `true` | rolling 전제 정책값 |
| `ceph_allow_reboot` | `false` | 재부팅 허용 여부 |
| `ceph_patch_batch_size` | `1` | 배치 크기 정책값 |
| `ceph_patch_packages` | ceph 관련 패키지 | 패치 대상 |

## 세부 진행단계

1. `ceph health`로 클러스터 상태를 조회합니다.
2. `apt-cache policy`로 대상 패키지 후보 버전을 조회합니다.
3. 패치 모드, 목표 버전, 요구 health, 현재 health를 report로 출력합니다.
4. enforce + 비-report 모드에서 health 기준을 assert로 검증합니다.
5. `security_only` 또는 `point_release` 모드에서 대상 패키지를 latest로 업그레이드합니다.
6. `specific_version` 모드에서 `ceph_target_version` 버전을 설치합니다.
7. `/var/run/reboot-required`를 확인합니다.
8. 재부팅 허용 시 reboot를 수행합니다.

## 단일기능 실행방법

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags ceph_patch \
  --limit ceph_hosts \
  --check --diff
```

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags ceph_patch \
  --limit ceph_hosts \
  -e "enable_ceph_patch=true security_action_mode=enforce ceph_patch_mode=security_only"
```
