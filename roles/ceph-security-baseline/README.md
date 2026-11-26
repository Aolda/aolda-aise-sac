# ceph-security-baseline

Ceph 호스트 보안의 기존 기능을 조회하고 선택적으로 적용합니다. 기본은 report이며 운영 서버 적용 완료를 의미하지 않습니다.

- [운영 방법·변수 변경·미지원 범위](../../docs/kvm-ceph-hardening.md)
- [시험 기준·결함 검출률·누락 가능 유형](../../docs/kvm-ceph-testing.md)
- [현재 변수 기본값](defaults/main.yml)
- [실행 작업 목록](tasks/main.yml)

실제 변경에는 apply_policy=true, 역할 적용 모드 및 기능별 활성화 조건이 필요합니다. 명시적 --check는 변경하지 않습니다. Ubuntu 24.04 호스트 패키지 설치 방식만 적용 대상으로 지원하며, 컨테이너 기반 배포는 별도 작업입니다.
