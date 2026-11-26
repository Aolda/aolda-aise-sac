# 실제 Ceph 설치 시험

## 목적과 범위

사용자의 2026-11-27 추가 지시에 따라 기존 Ubuntu 24.04 DevStack 시험 서버에 Ceph 19.2.3을 설치했습니다. 기존 5단계 검증 PR에 추가한 시험이며 QEMU 신규 기능 확장은 포함하지 않습니다.

Ceph MON(클러스터 상태 관리), MGR(관리 서비스), OSD(객체 저장 서비스)를 각각 하나씩 실행합니다. 모든 Ceph 수신 주소는 `127.0.0.1`입니다. OSD는 `/var/lib/ceph/osd/ceph-0/block`의 3 GiB 일반 파일을 사용합니다. 실제 디스크·파티션·기존 Cinder 루프 장치를 초기화하지 않았습니다. 복제본 없는 단일 노드 시험 구성으로 운영 배포 지침이 아닙니다.

## 설치 방식과 자체판단

- 기존 librados/librbd와 같은 Ubuntu 패키지 버전 `19.2.3-0ubuntu0.24.04.3`을 선택했습니다. 패키지 관리자 확인 결과 신규 47개, 업그레이드 0개, 제거 0개입니다.
- `ceph-mon ceph-mgr ceph-osd ceph-common`을 `--no-upgrade --no-remove --no-install-recommends`로 설치했습니다. 기존 서비스 자동 재시작을 요청하지 않았고 서버를 재부팅하지 않았습니다.
- 국내 HTTP 미러가 응답하지 않아 기존 패키지 목록의 정확한 파일을 Ubuntu 공식 HTTPS 미러에서 내려받아 크기·목록 해시를 확인했습니다. 호스트 저장소 설정은 바꾸지 않았습니다.
- 설치는 프로젝트 보안 역할에 넣지 않았습니다. `tests/kvm_ceph/lab/bootstrap.sh`는 명시적인 `AISE_CEPH_LAB_CONFIRMED=yes`를 요구하며 기존 Ceph 설정/시험 저장소가 있으면 중단하는 **일회성 시험 준비 스크립트**입니다. 재실행 가능한 보안 역할과 구분합니다.
- CephX 인증을 유지한 채 `cephx,cephx`라는 동일 인증 방식의 중복 목록으로 구성 차이를 주입합니다. 인증 없는 클러스터를 가동하지 않고도 실제 구성 조회·변경·반복 적용을 확인하기 위한 선택입니다. `none`에서 `cephx`로 전환하는 서비스 중단/재시작 절차는 검증한 것으로 취급하지 않습니다.
- 최초 구성에서 클라이언트 요구 인증의 기본값이 `cephx, none`임을 확인했습니다. 시험 초기 조건을 명시적인 `cephx`로 맞췄습니다.
- 최초 저장소 구성에는 기본 CRUSH(데이터 배치 계층)의 root 연결이 빠져 쓰기 시간 초과가 발생했습니다. `root=default`를 추가한 뒤 실제 쓰기/읽기 비교로 수정 결과를 검증했습니다. 스크립트 전체를 새 서버에서 다시 설치하는 시험은 하지 않았습니다.

구성 근거: [Ceph 공식 수동 배포 문서](https://docs.ceph.com/en/squid/install/manual-deployment/), [관리 서비스 구성 문서](https://docs.ceph.com/en/squid/mgr/administrator/). 일반 파일 기반 단일 저장소는 이 프로젝트의 격리 시험용 선택입니다.

## 재실행

인벤토리에 `baseline_test` 그룹과 시험 서버의 접속 설정을 넣습니다. 실제 주소·인증키는 저장소에 포함하지 않습니다. 아래 명령은 저장소 루트에서 실행합니다.

```bash
ansible-playbook tests/kvm_ceph/ceph_live.yml -i /absolute/test-inventory.ini \
  -e baseline_test_confirmed=true
ansible-playbook tests/kvm_ceph/ceph_live_keyring.yml -i /absolute/test-inventory.ini \
  -e baseline_test_confirmed=true
ansible-playbook tests/kvm_ceph/ceph_live_policy.yml -i /absolute/test-inventory.ini \
  -e baseline_test_confirmed=true -e apply_policy=true -e security_action_mode=enforce
# 같은 정책을 두 번째 실행하여 changed=0 확인
ansible-playbook tests/kvm_ceph/ceph_live_policy.yml -i /absolute/test-inventory.ini \
  -e baseline_test_confirmed=true -e apply_policy=true -e security_action_mode=enforce
# 실제 CLI(명령줄) 점검 모드
ansible-playbook tests/kvm_ceph/ceph_live_policy.yml -i /absolute/test-inventory.ini \
  -e baseline_test_confirmed=true -e apply_policy=true -e security_action_mode=enforce --check
```

설정 차이가 있는 상태의 명령줄 점검도 다음 순서로 재현할 수 있습니다. 마지막 실제 적용 명령으로 주입한 차이를 복구한 뒤 위의 전체 역할을 한 번 더 실행해 변경 0건을 확인합니다.

```bash
ansible-playbook tests/kvm_ceph/ceph_check_state.yml -i /absolute/test-inventory.ini \
  -e baseline_test_confirmed=true -e ceph_check_operation=seed
ansible-playbook tests/kvm_ceph/ceph_live_policy.yml -i /absolute/test-inventory.ini \
  -e baseline_test_confirmed=true -e apply_policy=true -e security_action_mode=enforce --check
ansible-playbook tests/kvm_ceph/ceph_check_state.yml -i /absolute/test-inventory.ini \
  -e baseline_test_confirmed=true -e ceph_check_operation=verify
ansible-playbook tests/kvm_ceph/ceph_live_policy.yml -i /absolute/test-inventory.ini \
  -e baseline_test_confirmed=true -e apply_policy=true -e security_action_mode=enforce
```

각 시험은 저장된 시험 클러스터 식별자와 현재 `ceph fsid`를 비교합니다. 일반 운영 클러스터에 실행하지 마십시오. 전체 역할 시험에서는 계정·SSH·패치·SELinux 기능을 명시적으로 끕니다. 이 기능들의 실환경 시험 통과를 의미하지 않습니다.

점검 모드는 실제 `--check`로 검증합니다. 작업 단위의 `check_mode: true`만 지정하는 방식은 `ansible_check_mode` 전역 변수와 같지 않아 적용 후 검증이 실행될 수 있습니다. 이 별도 호출 방식은 이번 지원/통과 범위가 아닙니다.

## 시험 선정 관점

|시험|검증 관점|
|---|---|
|실제 설정 차이 + 보고/적용 비활성|변경 필요 여부를 보고하되 실제 구성 DB(설정 저장소)를 변경하지 않는지|
|최초 적용 + 동일 조건 반복|실제 Ceph 명령이 세 설정만 복구하며 재실행에는 변경 명령이 없는지|
|실행 중인 MON 설정|구성 저장소 조회와 별도로 실제 서비스가 CephX 값을 보고하는지|
|실제 관리자 keyring 변조|인증 비밀 파일의 권한만 바뀐 경우 복구하며 재실행에는 변경이 없는지|
|잘못된 키·권한 없는 명령|인증 실패와 권한 실패를 각각 확인하고 시간 초과를 거부 성공으로 세지 않는지|
|허용된 객체 입출력|제한된 클라이언트가 허용된 풀에서 실제 쓰기·읽기를 수행하고 내용이 일치하는지|
|실제 클라이언트 키 배포|생성된 키를 기존 copy 작업으로 배포하고 재배포 시 ctime/파일 식별자가 유지되는지|
|전체 역할 재실행·명령줄 점검|개별 작업 밖의 연결 상태와 변경 집계를 실제 실행으로 확인하는지|

Hitting Rate(결함 검출률)는 기존 대표 결함 주입 12/12와 구분해 해석합니다. 이번 실제 클러스터 시험에는 별도의 신규 결함 주입 검출률을 측정하지 않았습니다. 시험 통과율을 결함 검출률이나 코드 커버리지로 표기하지 않습니다.

## 유지·정리와 한계

시험 클러스터와 `aise-security-test` 풀, 제한된 `client.aise-test` 계정, 시험 객체는 후속 검증을 위해 유지합니다. 잘못된 키 및 배포 시험용 복사본은 시험 후 삭제합니다. 관리자/클라이언트 인증키의 내용을 로그·PR·저장소에 기록하지 않습니다.

확인/중지 명령(시험 서버 내부, 관리자 권한):

```bash
ceph -s
ceph health detail
systemctl status ceph-mon@aise-test ceph-mgr@aise-test ceph-osd@0
# 이후 시험을 끝내고 자원을 중지할 때만 실행
systemctl stop ceph-osd@0 ceph-mgr@aise-test ceph-mon@aise-test
```

`HEALTH_WARN`의 복제본 없음 경고는 시험 구조의 한계로 그대로 보고합니다. 경고를 숨기거나 HEALTH_OK를 주장하지 않습니다. 다중 노드 정족수·장애 복구, 무인증에서 인증 전환, 패키지 업그레이드/롤링 재시작/호스트 재부팅, 서로 다른 Ceph 버전, 외부 네트워크·장애 지연·성능, 로컬 설정 파일이 중앙 설정을 덮어쓰는 환경은 미검증입니다.
