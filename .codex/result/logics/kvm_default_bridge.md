# kvm_default_bridge

## 기능 한줄정리

libvirt `default` network와 `virbr0` 사용 여부를 점검하고, 필요 시 autostart 해제/중지/정의 삭제를 단계적으로 수행합니다.

## 적용방법

1. 기본값은 비활성화되어 있으므로 `enable_kvm_default_bridge_disable: true`가 필요합니다.
2. report 모드에서 `virsh net-info` 결과를 먼저 확인합니다.
3. 실제 변경은 `security_action_mode: enforce`에서만 수행합니다.
4. `destroy`, `undefine`은 별도 boolean guard를 true로 설정해야 합니다.

## 제공인자

| 인자 | 기본값 | 설명 |
|---|---:|---|
| `enable_kvm_default_bridge_disable` | `false` | 기능 활성화 여부 |
| `kvm_libvirt_default_network_name` | `default` | 대상 libvirt network |
| `kvm_disable_network_autostart` | `true` | autostart 해제 여부 |
| `kvm_destroy_active_network` | `false` | active network 중지 여부 |
| `kvm_undefine_default_network` | `false` | network 정의 삭제 여부 |
| `kvm_default_bridge_action` | `report` | `report`, `disable`, `destroy`, `undefine` |

## 세부 진행단계

1. `virsh net-info <network>`로 대상 network 존재 여부를 조회합니다.
2. network 이름, action, 존재 여부, 상세 상태를 report로 출력합니다.
3. enforce + disable/destroy/undefine 모드에서 autostart를 해제합니다.
4. enforce + destroy/undefine 모드이고 `kvm_destroy_active_network`가 true이면 network를 중지합니다.
5. enforce + undefine 모드이고 `kvm_undefine_default_network`가 true이면 network 정의를 삭제합니다.

## 단일기능 실행방법

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags kvm_default_bridge \
  --limit kvm_hosts \
  --check --diff \
  -e "enable_kvm_default_bridge_disable=true"
```

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags kvm_default_bridge \
  --limit kvm_hosts \
  -e "enable_kvm_default_bridge_disable=true security_action_mode=enforce kvm_default_bridge_action=disable"
```
