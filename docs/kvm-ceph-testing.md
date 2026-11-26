# KVM·Ceph 시험 기준

## 시험 구분과 선정 기준

|종류|관점|한계|
|---|---|---|
|계정·키 단위 시험|숫자 경계값, 예외 계정 우선순위, 불명 상태, 기존 키 보존·빈 목록·필수 키|실제 계정 저장소 및 SSH 인증을 대체하지 않음|
|파일·복구 단위 시험|백업 충돌·미완성·점검 무변경·SSH 실패 복구|sshd 실행 결과를 대체하므로 실제 Include/Match 동작은 별도|
|계약 검사|중요 실행 조건·단일 호스트 배치·비밀 출력 차단의 누락 방지|조건 문자열 존재만으로 실제 동작을 보장하지 않음|
|실제 Ansible 로컬 통합|임시 파일 권한 첫 적용/재적용/변경 복구, report/check 쓰기 차단|운영체제 계정·방화벽·서비스 변경은 실행하지 않음|
|상태를 가진 대체 명령 통합|Ceph 조회/변경 호출 횟수, 두 번째 실행, 실패 주입|Ceph 실제 인증 프로토콜/클러스터 동작 검증이 아님|
|보고서 회귀 시험|정상 조회와 기준 충족 구분, 미실행/불명 상태, 기존 역할 출력 유지|전체 보안 정책 준수율 측정이 아님|
|결함 주입 시험|수정한 오류를 다시 넣었을 때 테스트가 탐지하는지 확인|등록한 대표 결함만 측정하며 모든 가능한 결함의 커버리지는 아님|

## 실행

```bash
python -m unittest discover -s tests/kvm_ceph -v
python tests/kvm_ceph/mutation_check.py --output /tmp/kvm-ceph-mutations.json
bash tests/smoke/test_report_without_server.sh localhost
ansible-playbook --syntax-check playbooks/security_baseline.yml -i inventory/hosts.yml
ansible-playbook --syntax-check playbooks/kvm_account_audit.yml -i inventory/hosts.yml
```

Python 환경에 ansible-core와 PyYAML이 필요하고, 전체 문법 검사에는 requirements.yml의 컬렉션이 필요합니다. 로컬 통합 시험은 테스트 전용 임시 파일과 가짜 명령만 사용합니다. 운영 계정으로의 권한 상승은 ansible_become=false로 차단합니다.

## Hitting Rate(결함 검출률)의 정의

주 지표는 `테스트 실패로 검출한 주입 결함 수 / 유효하게 주입한 대표 결함 수`입니다. 예를 들어 숫자 비교를 문자열 비교로 되돌리거나, 키 교체 확인을 제거하거나, SSH 유효값 검증을 무시하는 결함을 넣습니다. 문법/가져오기/시험 준비 오류는 검출 성공으로 계산하지 않습니다. 정상 코드의 시험 통과를 먼저 확인한 뒤 실행합니다.

보조 지표인 등록 시험 실행률과 통과율은 별도로 보고합니다. 이 값들은 코드 줄/분기 커버리지나 전체 보안 요구사항 충족률이 아닙니다. 각 subTest 입력을 별도 테스트로 부풀리지 않습니다. `mutation_check.py --stage N --repo /path/to/stage-worktree`로 해당 단계 소스에 대한 결과를 다시 측정할 수 있습니다.

## 누락 가능 유형과 실환경 보류

- 외부 계정 조회 서비스(LDAP/NSS), 로그인 이력 형식·배포판 차이, 사용자 기본 그룹 없음.
- 실제 SSH 키 인증 및 sudo 명령 허용/우회, Include/Match 조건별 SSH 유효값.
- UFW 규칙의 IPv4/IPv6 혼합, 접속 단절, libvirt 네트워크 상태 전환.
- SELinux 부팅 후 상태, 실제 패키지 저장소·버전·재부팅·서비스 시작.
- 다중 Ceph 노드 정족수·장애·복귀·지연, 실행 중 QEMU 프로세스 코드 반영.
- 동시에 두 실행이 진행되는 경쟁, 백업 도중 로그 변경, 복잡한 logrotate include/문법.

실환경 시험이 실행되지 않은 경우 보고서와 PR에 미실행으로 명시하며, 이를 통과율 분모에서 숨겨 전체 검증 완료로 주장하지 않습니다.

## 이번 실행 결과

[검증 결과 및 실제 시험 서버 범위](kvm-ceph-validation-results.md)에 로컬 63개, 대표 결함 12개, 실환경 완전 수행 10개 유형·부분 수행 1개 유형과 미수행 5개 유형을 구분해 기록했습니다.

실제 Ceph 설치 후 추가 검증의 재현 절차와 시험 선정 이유는 [Ceph 실환경 시험](ceph-live-lab.md)을 참고하십시오.
