# KVM·QEMU·Ceph 기존 기능 보완 운영 안내

## 범위

KVM/QEMU는 `kvm-account-audit`, Ceph는 `ceph-security-baseline`에서 관리합니다.
QEMU 프로세스 격리·가상 디스크·관리 연결 보안, Ceph 키 회전, 가상머신 자동 이동은 이번 변경에 포함하지 않습니다.
소스 코드와 자동 시험 결과를 실제 운영 환경 적용 완료로 해석하지 않습니다.

## 실행 계약

- 기본 `apply_policy=false`, `security_action_mode=report`입니다. 보고 모드는 대상 설정을 변경하지 않습니다.
- 실제 변경은 `apply_policy=true`, `security_action_mode=enforce`와 기능별 조건이 모두 필요합니다.
- 계정 삭제는 `security_action_mode=delete`, `kvm_account_action=delete`, 명시적 퇴직 계정 목록을 사용합니다.
- 명시적 `--check`는 항상 실제 변경을 차단합니다. 읽기 전용 조회는 점검 모드에서도 실행합니다.
- 최초 enforce 전 Ubuntu 24.04와 실제 호스트 패키지 설치 방식을 확인하고 `kvm_installation_layout` 또는 `ceph_installation_layout`을 `host_packages`로 지정합니다. 컨테이너 기반 배포는 지원하지 않습니다.
- 기본 실행 파일은 `serial: 1`과 `any_errors_fatal: true`로 한 호스트씩 진행하며 실패 시 다음 호스트를 변경하지 않습니다.
- `--tags`는 기능을 선택합니다. `always` 태그의 사전 점검을 우회하지 마십시오.
- Ansible의 계정 조회는 로그인 이력에만 의존하므로 프로세스 전용·SSH 키 전용 계정의 실제 사용 여부 전체를 보장하지 않습니다. 허용/제외 목록을 먼저 구성하십시오.

```bash
ansible-galaxy collection install -r requirements.yml
ansible-playbook playbooks/security_baseline.yml -i inventory/hosts.yml --limit kvm_hosts
ansible-playbook playbooks/security_baseline.yml -i inventory/hosts.yml --limit ceph_hosts --tags ceph_keyring
```

대상은 예시 인벤토리에 직접 등록해야 합니다. 정책 파일은 명시적으로 `-e @/absolute/path/policy.yml`로 전달하거나 인벤토리/플레이북 기준 `group_vars`에 배치합니다. 프로젝트 루트의 예시 `group_vars`가 어떤 실행 위치에서도 자동 로드된다고 가정하지 마십시오.

## 기존 변수의 의미 변경

|항목|변경 후 동작|
|---|---|
|로그인 이력 없음|계정 생성 시점을 알 수 없으므로 자동 9999일 잠금 대신 검토 대상으로 보고|
|수동 잠금 스크립트|기본 비활성. 고정 경로의 정책 대상만 허용하며 비밀번호 잠금과 nologin 셸을 함께 적용. 실행 시 자동 삭제하지 않음|
|Ceph 관리자 기본값|sudo 그룹 자동 추가·비밀번호 없는 ALL 권한 기본 제공을 제거. 명시적 명령 목록이 없으면 관리자 적용 실패|
|Ceph 전체 권한|`ceph_admin_allow_full_sudo=true`인 경우에만 ALL/sudo/wheel 허용. 기존 그룹도 조회하며 기존 운영자 권한을 임의 회수하지 않음|
|authorized_keys|기본 추가·보존. 전체 교체는 `ceph_purge_unmanaged_keys=true`와 `ceph_authorized_keys_replace_confirmed=true` 필요|
|필수 관리 키|`ceph_authorized_keys_required`의 사용자별 키가 결과 목록에 남아야 함. 키는 로그에 출력하지 않음|
|패치 모드|`report`, `latest`, `specific_version`만 지원. `security_only`와 `point_release`는 범위를 보장하지 못하므로 명시적으로 거부|
|버전 하향 변경|`kvm_allow_package_downgrade` 또는 `ceph_allow_package_downgrade`를 명시해야 함|
|SELinux|이미 활성화된 환경의 실행 모드·영구 모드만 변경. 최초 활성화/정책 교체/무조건 재부팅은 하지 않음|
|로그 백업|`kvm_log_backup_enabled`와 별개로 `kvm_log_backup_run=true`, 안전한 `kvm_log_backup_id`가 필요. 같은 ID는 한 번만 생성|

관리자 정책을 변경하지 않고 Ceph 파일 권한만 적용하려면 기능 태그로 제한하거나 `enable_ceph_admin_user_policy=false`를 지정하십시오. 전체 역할에서 enforce를 켜면 기본 활성화된 기능들이 함께 적용됩니다.

## 패치 전제와 중단 조건

패치에는 기능 활성화, 적용 모드, `*_patch_maintenance_confirmed=true`, 단일 호스트 배치, 비어 있지 않은 `*_patch_precheck_commands`와 `*_patch_postcheck_commands`가 필요합니다. 각 명령은 문자열 배열(argv)의 목록이며 실패 코드는 작업을 중단합니다. 이 명령은 운영자가 제공하는 읽기 전용 검증 절차입니다.

- KVM 사전 점검은 작업 수용 중단·가상머신 유지보수 준비를 확인해야 합니다. 가상머신 이동을 역할이 자동 수행하지는 않습니다.
- Ceph 사전 점검은 해당 노드의 데몬 종류와 클러스터 구성에 맞는 중지 가능 여부·정족수·복제 상태를 확인해야 합니다. 단순 health 조회만으로 이를 대체하지 마십시오.
- 사후 점검은 서비스 정상 기동과 애플리케이션의 실제 사용 가능 여부를 확인해야 합니다.
- 역할은 추가로 KVM 실행 가상머신 목록 보존, 지정 패키지 버전, Ceph `HEALTH_OK` 복귀를 확인합니다.
- 자동 재부팅은 이번 패키지 변경과 재부팅 필요 파일이 함께 존재하고 재부팅 허용이 설정된 경우에만 수행합니다.
- 노드별 직렬화는 무중단 보장이 아닙니다. 패치 적용 후 QEMU 실행 프로세스에 새 코드가 반영됐는지 역시 운영 검증 대상입니다.

## 복구 및 산출물

SSH 설정은 전체 문법과 유효값을 검증합니다. reload 전 검증이 실패하면 이전 내용·권한·소유권을 복구하고, 새 파일은 제거합니다. 기존 파일 백업은 `.aise-backup`에 0600으로 저장합니다. reload 이후 연결 상실 시에는 콘솔 등 별도 경로를 통한 복구가 필요합니다. 계정 삭제와 패키지 하향 변경은 자동으로 되돌리지 않습니다.

로그 스냅샷은 대상 서버 내부 저장이며 원본 경로를 보존합니다. 동일 작업 ID는 재복사하지 않습니다. 로그를 복사하는 도중 발생하는 기록까지 원자적으로 보존하는 데이터베이스식 스냅샷은 아닙니다. 보존 기간에 따른 삭제는 이번 변경에서 자동화하지 않으며 운영자가 보관 용량을 관리합니다. 미완성 디렉터리는 덮어쓰지 않고 오류로 알립니다.

## 보고서 해석과 미완료 검증

KVM/Ceph 보고서는 정책 판정과 작업 실행 기록을 분리합니다. 기준 충족·조치 필요·적용 후 충족·점검/적용 실패·점검 불가·미실행으로 표시합니다.

현재 자동 비교 근거를 제공하는 항목은 KVM 미사용/퇴직 계정 검토와 SSH 연결 응답 설정, Ceph keyring·설정 파일 권한과 CephX입니다. 계정 잠금 성공이 미사용 계정 검토 완료를 의미하지는 않습니다. 셸 TMOUT, UFW 전체 유효 규칙, Ceph 전체 sudo 권한 등 종합 판정이 없는 항목은 점검 불가로 남습니다. 개별 작업 성공으로 이 상태를 충족으로 바꾸지 않습니다.

실제 KVM·Ceph 서버, 네트워크 연결, 재부팅, 다중 노드 실패 복구는 별도 시험 환경에서 검증해야 합니다. 등록 시험 목록과 결함 검출률 측정은 [시험 안내](kvm-ceph-testing.md)를 참고하십시오.
