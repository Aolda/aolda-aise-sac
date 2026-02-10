# KVM 계정 감시 역할에 대한 README

## 개요

`kvm-account-audit` 역할은 KVM 하이퍼바이저 호스트에서 30일 이상 사용되지 않은 계정을 식별하고, 감시 보고서 및 자동화 스크립트를 생성합니다.

## 기능

1. **미사용 계정 식별**
   - KVM 제어 그룹(`kvm`, `qemu`, `libvirt`)에 속한 계정 조회
   - `lastlog` 기반 마지막 접속 시간 추출
   - 30일 이상 미사용 계정 필터링

2. **감시 보고서 생성 (Markdown)**
   - 미사용 계정 목록 (내림차순: 미접속 기간)
   - 60일 이상 미사용 계정 식별 및 권고사항
   - 타임스탬프 및 호스트 정보 포함

3. **자동 적용 스크립트 생성**
   - 대상 계정을 자동으로 잠금 처리
   - 멱등성 보장 (중복 실행 안전)
   - 스크립트 자체 삭제 (자정소 정리)

4. **조건부 처리**
   - 미사용 계정이 없으면 작업 완료
   - 보고서/스크립트 생성 불필요

## 실행 방법

### 1. 인벤토리 설정

`inventory/hosts.yml`에 KVM 호스트 정의:

```yaml
[kvm_hosts]
kvm-hypervisor-01 ansible_host=192.168.1.100 ansible_user=root
```

### 2. 플레이북 실행

```bash
ansible-playbook playbooks/kvm_account_audit.yml -i inventory/hosts.yml
```

### 3. 생성된 산출물 확인

- **보고서**: `/tmp/kvm_audit_reports/kvm_account_audit_*.md`
- **스크립트**: `/home/<user>/apply_account_restrictions_*.sh`

### 4. 자동 조치 적용

```bash
bash apply_account_restrictions_*.sh <username>
```

예:
```bash
bash apply_account_restrictions_20260210T153045.sh kvmuser01
```

## 설정 항목

`group_vars/kvm_hosts.yml`에서 다음 항목 수정 가능:

| 항목 | 기본값 | 설명 |
|------|-------|------|
| `inactivity_threshold_days` | 30 | 미사용 계정 감지 임계값 (일) |
| `restriction_threshold_days` | 60 | 사용제한 권고 임계값 (일) |
| `report_dir` | `/tmp/kvm_audit_reports` | 보고서 저장 경로 |
| `target_groups` | `[kvm, qemu, libvirt]` | 모니터링 대상 그룹 |

## 멱등성

- 동일한 플레이북을 여러 번 실행해도 시스템 상태가 일관되게 유지됩니다.
- 자동 적용 스크립트는 이미 잠금된 계정을 건너뜁니다.

## 보안 정책

- **30-60일 미사용**: 계속 모니터링 (계정 소유자 확인 필수)
- **60일 이상 미사용**: 즉시 잠금 권고 (악의적 접근 위험)
- **영구 삭제는 미지원**: 계정 복구 가능성을 위해 잠금만 수행

## 로그 및 감시

- 모든 계정 조치는 `/var/log/kvm_account_audit_actions.log`에 기록됩니다.
- Ansible 실행 로그는 표준 Ansible 로깅 메커니즘 활용

## 주의사항

1. **검토 필수**: 자동 조치 전에 보고서를 신중하게 검토하세요.
2. **승인 프로세스**: 계정 잠금 전 관리자/소유자 승인 필수입니다.
3. **테스트**: 실운영 환경 적용 전에 테스트 환경에서 검증하세요.

## 문제 해결

### 보고서가 생성되지 않음
- `inactivity_threshold_days` 값이 적절한지 확인
- 타겟 그룹에 속한 계정이 있는지 확인
- `lastlog` 명령 실행 권한 확인

### 스크립트 실행 실패
- Root 권한으로 실행하는지 확인
- 계정이 정말 존재하는지 확인 (`id <username>`)
- 파일 권한 확인 (`ls -l apply_account_restrictions_*.sh`)
