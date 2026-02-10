# KVM 계정 감시 역할에 대한 README

## 개요

`kvm-account-audit` 역할은 KVM 하이퍼바이저 호스트에서 30일 이상 사용되지 않은 계정을 식별하고, 감시 보고서 및 자동화 스크립트를 생성합니다.

## 기능

1. **미사용 계정 식별**
   - KVM 제어 그룹(`kvm`, `qemu`, `libvirt`)에 속한 계정 조회
   - `lastlog` 기반 마지막 접속 시간 추출
   - 30일 이상 미사용 계정 필터링 및 정렬

2. **자동 계정 잠금 처리 (60일+ 미사용)**
   - 60일 이상 미사용 계정 자동 식별
   - 계정 자동 잠금 처리 (`usermod -L`)
   - 보고서에 잠금 상태 기록
   - 멱등성 보장 (이미 잠금된 계정 중복 처리 방지)

3. **감시 보고서 생성 (Markdown)**
   - 미사용 계정 목록 (내림차순: 미접속 기간)
   - 자동 잠금된 계정 명시
   - 30-60일 미사용 계정 모니터링 목록
   - 타임스탬프 및 호스트 정보 포함
   - 복구 절차 안내

4. **선택적 수동 잠금 스크립트**
   - 30-60일 미사용 계정의 선택적 잠금용 스크립트 제공
   - 인자로 받은 계정만 잠금 처리
   - 자체 삭제 기능 포함

5. **조건부 처리**
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

### 3. 자동 처리 결과 확인

플레이북 실행 시 다음과 같이 진행됩니다:

1. **60일+ 계정 자동 잠금**: 조건을 만족하는 계정 자동 처리
2. **보고서 생성**: 감시 결과를 Markdown으로 기록
3. **스크립트 생성**: 선택적 수동 잠금용 스크립트 배포

### 4. 생성된 산출물 확인

- **보고서**: `/tmp/kvm_audit_reports/kvm_account_audit_*.md`
  - 자동 잠금된 계정 목록
  - 모니터링 중인 계정 목록
  - 복구 절차 안내

- **스크립트** (선택사항): `/home/<user>/apply_account_restrictions_*.sh`
  - 30-60일 미사용 계정의 수동 잠금용

### 5. 선택적 수동 조치 (필요시)

30-60일 미사용 계정 중 추가로 잠금이 필요한 경우:

```bash
bash apply_account_restrictions_*.sh <username>
```

예:
```bash
bash apply_account_restrictions_20260210T153045.sh kvmuser02
```

## 자동 잠금 프로세스

### 프로세스 흐름

```
플레이북 실행
    ↓
미사용 계정 식별 (30일+)
    ↓
60일+ 계정 필터링
    ↓
자동 계정 잠금 (user 모듈)
    ↓
잠금 결과 로깅
    ↓
보고서 생성 (잠금 상태 포함)
    ↓
완료
```

### 멱등성 보장 방식

- `user` 모듈의 `password_lock: yes` 사용
- 이미 잠금된 계정은 상태 변경 없음
- 여러 번 실행해도 안전 (중복 잠금 불가)

## 설정 항목

`group_vars/kvm_hosts.yml`에서 다음 항목 수정 가능:

| 항목 | 기본값 | 설명 |
|------|-------|------|
| `inactivity_threshold_days` | 30 | 미사용 계정 감지 임계값 (일) |
| `restriction_threshold_days` | 60 | **자동 잠금 임계값** (일) |
| `report_dir` | `/tmp/kvm_audit_reports` | 보고서 저장 경로 |
| `target_groups` | `[kvm, qemu, libvirt]` | 모니터링 대상 그룹 |

## 멱등성

- 동일한 플레이북을 여러 번 실행해도 시스템 상태가 일관되게 유지됩니다.
- **자동 잠금**: Ansible `user` 모듈로 보장 (중복 방지)
- **수동 스크립트**: 계정 상태 사전 확인 후 처리

## 보안 정책

| 기준 | 조치 | 설명 |
|------|------|------|
| **30-60일 미사용** | 📊 모니터링 | 관리자 검토 후 필요시 수동 처리 |
| **60일 이상 미사용** | 🔒 **자동 잠금** | 플레이북 실행 시 즉시 처리 |

- **자동 잠금의 목적**: 악의적 접근 위험 감소
- **영구 삭제는 미지원**: 계정 복구 가능성을 위해 잠금만 수행
- **복구 방법**: `usermod -U` 또는 `passwd -u`로 언제든 복구 가능

## 로그 및 감시

- 모든 계정 조치는 다음 위치에 기록됩니다:
  ```
  /var/log/kvm_account_audit_actions.log
  ```
- Ansible 실행 로그: 표준 Ansible 로깅 메커니즘 활용
- 보고서: Markdown 형식으로 각 실행마다 새로 생성

## 주의사항

1. **자동 잠금**: 60일+ 계정은 명시적 승인 없이 자동 처리됩니다.
2. **검토 권장**: 플레이북 실행 후 보고서를 반드시 검토하세요.
3. **복구 절차**: 잠금된 계정 복구는 관리자에게만 권한이 있어야 합니다.
4. **테스트**: 실운영 환경 적용 전에 테스트 환경에서 검증하세요.

## 문제 해결

### 자동 잠금이 되지 않음
- `restriction_accounts` 변수가 올바르게 생성되었는지 확인
- `-v` 옵션으로 Ansible 실행하여 디버그 정보 확인
  ```bash
  ansible-playbook playbooks/kvm_account_audit.yml -i inventory/hosts.yml -v
  ```

### 보고서가 생성되지 않음
- `inactivity_threshold_days` 값이 적절한지 확인
- 타겟 그룹에 속한 계정이 있는지 확인
- `lastlog` 명령 실행 권한 확인

### 스크립트 실행 실패
- Root 권한으로 실행하는지 확인
- 계정이 정말 존재하는지 확인 (`id <username>`)
- 파일 권한 확인 (`ls -l apply_account_restrictions_*.sh`)
