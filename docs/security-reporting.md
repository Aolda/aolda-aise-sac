# 보안조치 Markdown 보고서

보안 playbook은 기본적으로 실제 시스템을 변경하지 않는 보고서 작성 모드로 실행됩니다.
실행 결과는 role마다 하나씩 프로젝트 루트의
`reports/REPORT.ROLE.YYYYMMDD_HHMMSS.md`에 저장됩니다.

## 실행 모드

기본 실행은 `apply_policy=false`이며 play 전체가 Ansible check mode로 동작합니다.

```bash
ansible-playbook playbooks/security-policy-2026.yml \
  -i inventory/security-policy-2026.example.ini
```

실제 조치를 적용하려면 반드시 `apply_policy=true`를 지정합니다.

```bash
ansible-playbook playbooks/security-policy-2026.yml \
  -i inventory/security-policy-2026.example.ini \
  -e apply_policy=true
```

wrapper를 사용할 수도 있습니다.

```bash
./run-security-policy.sh \
  --apply-policy=false \
  -i inventory/security-policy-2026.example.ini

./run-security-policy.sh \
  --apply-policy=true \
  -i inventory/security-policy-2026.example.ini
```

`--check`를 함께 지정하면 `apply_policy=true`여도 보고서에는 실제 자동적용이 수행되지
않은 것으로 기록됩니다.

## 보고서 설정

`ansible.cfg`의 `[callback_security_report]`에서 기본값을 변경할 수 있습니다.

```ini
[callback_security_report]
report_dir = reports
report_title = 보안조치 결과 보고서
```

환경 변수 `AISE_REPORT_DIR`, `AISE_REPORT_TITLE` 또는 play 변수 `report_dir`,
`report_title`도 지원합니다. play 변수가 가장 마지막에 적용됩니다.

각 보고서는 해당 role의 task 실행 결과를 대상 호스트별로 집계합니다.

- check mode에서 변경 예정인 task 또는 실패한 task: 조치 대상
- 변경 없이 성공한 task: 조치 완료
- 적용 모드에서 실제 변경에 성공한 task: 조치 성공
- 실패 또는 접근 불가 task: 조치 실패
- 조건에 의해 건너뛴 task: 세부현황에는 남지만 완료/조치 필요 통계에서는 제외

## 서버 없이 보고서 기능 테스트

실제 운영 서버가 없는 경우 localhost 또는 Docker 컨테이너를 사용해 보고서 생성,
callback, 통계 분기와 role/host별 세부현황을 검증할 수 있습니다. 테스트 inventory를
사용하면 `run-security-policy.sh`가 운영 playbook 대신 무해한
`tests/report-validation.yml`을 자동으로 선택합니다.

### localhost 테스트

localhost 테스트는 `apply_policy=false` 보고서 생성과 callback 동작 확인 전용입니다.
fixture role의 파일 task는 check mode에서 변경 예정 상태만 반환하며 실제 파일을 만들지
않습니다.

```bash
./run-security-policy.sh --apply-policy=false \
  -i inventory/local-report-test.ini
```

자동 검증 스크립트는 보고서 생성, 필수 제목, 3열 통계, 5열 통계 미출력,
role/host별 세부현황과 로컬 marker 미생성을 검사합니다.

```bash
./tests/smoke/test_report_without_server.sh localhost
```

안전을 위해 localhost 테스트에서 `--apply-policy=true`를 지정하면 wrapper와 테스트
role이 실행을 거부합니다.

### Docker 테스트

Docker 테스트는 Ubuntu 컨테이너를 임시 서버로 사용합니다. `apply_policy=true`에서
수행하는 조치는 컨테이너 내부 `/tmp/aise-report-test-*` marker 생성으로 제한됩니다.

```bash
docker run -dit --name sac-test-ubuntu ubuntu:24.04 sleep infinity
docker exec sac-test-ubuntu bash -c \
  "apt update && apt install -y python3 sudo"

./run-security-policy.sh --apply-policy=false \
  -i inventory/docker-report-test.ini

./run-security-policy.sh --apply-policy=true \
  -i inventory/docker-report-test.ini

docker rm -f sac-test-ubuntu
```

컨테이너 생성부터 정리까지 자동화하려면 다음 명령을 사용합니다.

```bash
./tests/smoke/test_report_without_server.sh docker
```

Docker daemon이 선택 사항인 개발 환경에서는 localhost 테스트만 실행하고, 사용 가능한
경우 Docker 테스트까지 실행할 수 있습니다.

```bash
./tests/smoke/test_report_without_server.sh all
```

`all` 모드는 Docker daemon을 사용할 수 없으면 Docker 테스트를 명시적으로 건너뜁니다.
localhost는 보고서 생성 검증용이며 실제 조치 분기는 반드시 Docker 같은 격리 환경에서
검증해야 합니다.

### 수동 완료 조건 확인

```bash
python3 -m py_compile plugins/callback/security_report.py
bash -n run-security-policy.sh
bash -n tests/smoke/test_report_without_server.sh

./run-security-policy.sh --apply-policy=false \
  -i inventory/local-report-test.ini

ls -al reports/
cat reports/REPORT.*.md
```
