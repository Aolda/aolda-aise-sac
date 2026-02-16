📁 Security Automation Architecture
1. Overview

본 프로젝트는 KISA 및 CIS Ubuntu 보안 기준을 기반으로
Ubuntu 서버 하드닝을 자동화하기 위해 Ansible Role 기반 구조로 설계되었다.

보안 통제를 다음 3가지 책임 영역으로 분리하였다:

Account Security – 계정 및 인증 정책

Config Security – 시스템 설정 및 서비스 보안

Audit – 보안 상태 점검 (Read-only)

각 역할(Role)은 독립적인 보안 모듈로 동작하도록 설계하였다.

2. Directory Structure
aolda-aise-sac/
│
├── docs/
│   ├── architecture.md
│   └── git-convention.md
│
├── inventory/
│   └── test.ini
│
├── playbooks/
│   └── test_security.yml
│
└── roles/
    ├── account_security/
    │   ├── defaults/
    │   │   └── main.yml
    │   ├── handlers/
    │   │   └── main.yml
    │   ├── tasks/
    │   │   ├── main.yml
    │   │   └── account.yml
    │   └── README.md
    │
    ├── config_security/
    │   ├── defaults/
    │   │   └── main.yml
    │   ├── handlers/
    │   │   └── main.yml
    │   └── tasks/
    │       ├── main.yml
    │       └── files.yml
    │
    └── audit/
        ├── defaults/
        │   └── main.yml
        └── tasks/
            ├── main.yml
            └── audit.yml

3. Role Design Principles
3.1 Responsibility Separation
Role	Responsibility
account_security	계정 정책, 비밀번호 정책, SSH 접근 제어
config_security	파일 권한, 서비스 비활성화, 포트 제한, 패치
audit	보안 상태 점검 (수정 없음)

각 Role은 자신의 책임 범위 내에서만 동작하도록 설계하였다.

3.2 tasks/main.yml 역할

각 Role은 반드시 tasks/main.yml을 엔트리 포인트로 가진다.

예:

- name: Apply account security hardening
  include_tasks: account.yml


Ansible은 Role 실행 시 자동으로 tasks/main.yml을 호출한다.

3.3 defaults 사용 원칙

각 Role은 정책 값을 defaults/main.yml에서 관리한다.

예:

패스워드 최소 길이

lockout 횟수

허용 IP 목록

audit 로그 경로

이를 통해 정책 변경과 로직을 분리하였다.

3.4 handlers 분리 원칙

서비스 재시작은 수정이 발생한 Role 내부에서만 수행한다.

예:

SSH 설정 변경 → account_security handler

rsyslog 변경 → config_security handler

Audit Role은 변경을 수행하지 않으므로 handler를 사용하지 않는다.

4. Execution Flow
Hardening Mode
account_security
        ↓
config_security
        ↓
audit

Audit Only Mode
audit


security_mode 변수를 통해 제어 가능하도록 설계할 수 있다.

5. Compliance Mapping

본 구조는 다음 기준을 참고하여 설계되었다:

KISA Linux Server 보안 가이드

CIS Ubuntu 24.04 Benchmark

적용 영역:

Access & Authentication

File Permissions

Logging

Service Hardening

6. Security Architecture Philosophy

본 구조는 단순한 설정 자동화가 아니라
다음 원칙을 기반으로 한다:

정책과 구현의 분리

수정과 점검의 분리

역할 기반 책임 분리

최소 권한 원칙

불필요 서비스 최소화

7. Future Improvements

UFW 기반 포트 화이트리스트 강화

SUID/SGID 정밀 점검 로직 고도화

Compliance Report 자동 생성

CI/CD 연동 시 audit_fail_on_findings 활용