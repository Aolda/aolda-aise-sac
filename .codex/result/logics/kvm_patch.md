# kvm_patch

## 기능 한줄정리

KVM/QEMU/libvirt 관련 패키지의 현재/후보 버전을 보고하고, 명시 모드에서 패치와 선택적 재부팅을 수행합니다.

## 적용방법

1. 기본 `kvm_patch_mode: report`로 패키지 후보 버전을 확인합니다.
2. 실제 패치는 `enable_kvm_patch: true`, `security_action_mode: enforce`가 필요합니다.
3. 패치 방식은 `security_only`, `latest`, `specific_version` 중 선택합니다.
4. 재부팅은 `kvm_allow_reboot: true`일 때만 수행됩니다.

## 제공인자

| 인자 | 기본값 | 설명 |
|---|---:|---|
| `enable_kvm_patch` | `false` | 패치 활성화 여부 |
| `kvm_patch_mode` | `report` | 패치 방식 |
| `kvm_patch_packages` | qemu/libvirt 패키지 | 패치 대상 |
| `kvm_target_package_versions` | `{}` | 특정 버전 지정 |
| `kvm_allow_reboot` | `false` | 재부팅 허용 여부 |
| `kvm_drain_compute_before_patch` | `true` | compute drain 전제 여부 |
| `kvm_patch_batch_size` | `1` | 배치 크기 정책값 |

## 세부 진행단계

1. `apt-cache policy`로 대상 패키지의 설치/후보 버전을 조회합니다.
2. 패치 모드, 대상 패키지, 재부팅 허용 여부를 report로 출력합니다.
3. enforce + `security_only` 또는 `latest` 모드에서 apt only-upgrade를 수행합니다.
4. enforce + `specific_version` 모드에서 지정 버전을 설치합니다.
5. `/var/run/reboot-required` 존재 여부를 확인합니다.
6. 재부팅이 필요하고 `kvm_allow_reboot`가 true이면 reboot를 수행합니다.

## 단일기능 실행방법

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags kvm_patch \
  --limit kvm_hosts \
  --check --diff
```

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags kvm_patch \
  --limit kvm_hosts \
  -e "enable_kvm_patch=true security_action_mode=enforce kvm_patch_mode=latest"
```
