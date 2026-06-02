# kvm_ip_restrict

## 기능 한줄정리

KVM 관리 포트 접근을 허용된 관리망/긴급망 CIDR로 제한하기 위한 Ubuntu `ufw` 정책을 구성합니다.

## 적용방법

1. 기본값은 비활성화되어 있으므로 `enable_kvm_ip_restrict: true`가 필요합니다.
2. 실제 적용은 `security_action_mode: enforce`와 `firewall_apply_mode: enforce`를 함께 설정합니다.
3. 현재 enforce 구현은 Ubuntu 24.04 기준 `ufw` backend만 지원합니다.
4. 기본 inbound deny는 `enable_default_deny: true`일 때만 적용합니다.

## 제공인자

| 인자 | 기본값 | 설명 |
|---|---:|---|
| `enable_kvm_ip_restrict` | `false` | 기능 활성화 여부 |
| `firewall_backend` | `ufw` | 방화벽 backend |
| `firewall_apply_mode` | `report` | 방화벽 적용 모드 |
| `allowed_management_cidrs` | `10.0.0.0/24` | 관리망 허용 CIDR |
| `emergency_access_cidrs` | `[]` | 긴급 접근 허용 CIDR |
| `allowed_service_ports` | SSH 22/tcp | 허용 포트 정책 |
| `default_inbound_policy` | `deny` | 기본 inbound 정책 |
| `enable_default_deny` | `false` | 기본 차단 적용 여부 |

## 세부 진행단계

1. 현재 방화벽 정책 변수와 CIDR 목록을 report로 출력합니다.
2. enforce 모드에서 backend가 `ufw`인지 검증합니다.
3. `ufw` 패키지를 설치합니다.
4. 관리망 CIDR과 긴급망 CIDR을 허용 포트 목록과 조합합니다.
5. 각 조합별로 `ufw allow from <CIDR> to any port <PORT> proto <PROTO>`를 실행합니다.
6. `enable_default_deny`가 true이면 기본 inbound 정책을 설정합니다.
7. `ufw --force enable`로 방화벽을 활성화합니다.

## 단일기능 실행방법

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags kvm_ip_restrict \
  --limit kvm_hosts \
  --check --diff \
  -e "enable_kvm_ip_restrict=true"
```

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags kvm_ip_restrict \
  --limit kvm_hosts \
  -e "enable_kvm_ip_restrict=true security_action_mode=enforce firewall_apply_mode=enforce"
```
