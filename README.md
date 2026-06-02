# AISE (Aolda Infrastructure Security Enhancement)

Ansible 기반 Security as Code 프로젝트 레포지토리입니다.

## 1. Introduction

> ### TL;DR
> 오픈소스 인프라 구성 요소에 보안 설정과 점검 자동화를 적용하는 Ansible 기반 Security as Code 프로젝트입니다.

<br>

## 2. Crews

<table>
  <tr>
    <td align="center"><a href="https://github.com/callme-waffle"><img src="https://avatars.githubusercontent.com/u/58645920?v=4" width="100px;" alt=""/><br /><sub><b>
김화균</b></sub></a><br /></td>
    <td align="center"><a href="https://github.com/su-biin"><img src="https://avatars.githubusercontent.com/u/218368342?s=400&v=4" width="100px;" alt=""/><br /><sub><b>
이수빈</b></sub></a><br /></td>
    <td align="center"><a href="https://github.com/m1cks"><img src="https://avatars.githubusercontent.com/u/29903378?v=4" width="100px;" alt=""/><br /><sub><b>
인승진</b></sub></a><br /></td>
    <td align="center"><a href="https://github.com/ag4710"><img src="https://avatars.githubusercontent.com/u/105358110?v=4" width="100px;" alt=""/><br /><sub><b>
이은환</b></sub></a><br /></td>
  </tr>
</table>

<br>

## 3. Product Info

### a. 프로젝트 개요

AISE는 Docker, DB, Kubernetes, OpenStack 등 인프라 구성 요소의 보안 점검과 안전한 수정 작업을 Ansible role과 playbook으로 자동화합니다. 기본 모드는 큰 틀의 보안 상태 점검과 파일 권한, 계정/권한 정리처럼 비교적 안전한 조치 중심이며, TLS 전환, Kubernetes manifest 변경, Docker daemon 보안 옵션, 암호화 같은 위험 작업은 고급 모드 변수로 분리합니다.

### b. 주요 기능

- 보안 기준에 맞춘 설정 적용 자동화
- 구성 요소별 사전 점검 및 검증 task 제공
- Molecule 기반 syntax/smoke 테스트 시나리오 제공
- 예시 inventory와 실행 playbook 제공

### c. 유사제품

- CSP Security Posture Management
- Infrastructure as Code 보안 점검 도구
- Ansible 기반 compliance automation

<br>

## 4. Repository Structure

| 경로 | 설명 |
| --- | --- |
| `docs/` | Git 규칙, Molecule 테스트, 블로그 템플릿 등 프로젝트 문서 |
| `inventory/` | Ansible 예시 인벤토리 |
| `playbooks/` | 보안 자동화 실행용 playbook |
| `roles/docker-security/` | Docker 호스트 보안 설정 role |
| `roles/db-security/` | MariaDB/MySQL 보안 설정 role |
| `roles/k8s-security/` | Kubernetes 보안 설정 role |
| `roles/*-security/` | OpenStack 컴포넌트 보안 설정 role |
| `molecule/` | Molecule 테스트 시나리오 |

## 5. Roles

| Role | 주요 내용 |
| --- | --- |
| `docker-security` | Docker 그룹 사용자 제한, service/socket/config 권한 관리, 런타임 컨테이너 점검 |
| `db-security` | DB 계정 정리, 권한 제한, 파일 권한, slow/error log 설정, 패스워드 정책/실행 계정 점검, 선택 패치 |
| `k8s-security` | Control Plane/API Server/etcd/Kubelet 상태 점검, 선택적 manifest/config 보안 설정, PSA/NetworkPolicy/Pod 보안 점검 |
| `keystone-security` | Keystone TLS, token hash, 요청 크기, admin token 관리 및 검증 task |
| `nova-security` | Nova Keystone 인증, TLS 선택 설정, Glance 통신 보안 및 검증 task |
| `neutron-security` | Neutron TLS 선택 설정 및 검증 task |
| `glance-security` | Glance Keystone 인증, TLS 선택 설정 및 검증 task |
| `cinder-security` | Cinder Keystone 인증, TLS 선택 설정, 요청 크기 관리 및 검증 task |
| `horizon-security` | 원본 50개 밖의 Horizon 확장 role. 기본 playbook 실행 대상에서 제외 |

## 6. GitHub Collaboration

### a. 커밋 규칙

커밋 메시지는 `prefix: content` 형식을 사용합니다.

예시:

```text
feat: add openstack security roles
docs: add molecule testing guide
fix: resolve playbook syntax issue
```

### b. PR(Pull Request) 규칙

작업 브랜치에서 PR로 `main`에 병합합니다. 자세한 규칙은 `docs/git-convention.md`를 참고합니다.

## 7. Workflow

- `main`: 안정화된 기준 브랜치
- `feat/*`, `refactor/*`, `fix/*`, `docs/*` 브랜치에서 작업 후 PR로 `main`에 병합

## 8. References

## 9. 실제 서버 적용 절차

### a. 실행 전 준비사항

1. 대상 서버를 inventory에 그룹별로 등록합니다.
   - DB: `db`
   - Docker: `docker`
   - Kubernetes: `k8s` 하위에 `k8s_control_plane`, `k8s_worker`
   - OpenStack 기본 실행: `keystone`, `nova`, `cinder`, `glance`, `neutron`
   - OpenStack 확장 role: `horizon`은 원본 50개 밖 항목이므로 기본 playbook에서 실행하지 않습니다.

Kubernetes 대상은 playbook의 `hosts: k8s`와 맞도록 children 그룹을 구성합니다.

```ini
[k8s:children]
k8s_control_plane
k8s_worker

[k8s_control_plane]
# control-plane1 ansible_host=10.0.0.40

[k8s_worker]
# worker1 ansible_host=10.0.0.41
```

2. Ansible collection을 설치합니다.

```bash
ANSIBLE_HOME=.ansible ansible-galaxy collection install -r requirements.yml
```

3. 실제 서버의 설정 파일 경로, 서비스명, 인증서 경로, openrc 경로를 group_vars 또는 host_vars에 정의합니다.
4. 운영 영향이 큰 변수는 기본값이 `false`입니다. 실제 적용 전 check mode와 diff를 먼저 확인합니다.
5. DB, OpenStack, Kubernetes 작업 전에는 DB dump, 설정 파일, static pod manifest, etcd snapshot 등 복구 가능한 백업을 준비합니다.

### a-1. 기본 모드와 고급 모드

| 모드 | 기본 성격 | 대표 항목 |
| --- | --- | --- |
| 기본 모드 | 원본 50개 기준의 점검과 안전한 수정 | DB 불필요 계정 제거, GRANT OPTION 제한, Docker group 정리, docker.sock/service/socket/daemon.json 권한, OpenStack `auth_strategy=keystone`, `max_request_body_size`, validate |
| 고급 모드 | 장애 가능성이 있는 선택 적용 | Kubernetes API Server manifest 수정, Admission Plugin, audit log, API/etcd/kubelet TLS, etcd encryption, NetworkPolicy/PSA 적용, Docker audit, Docker Content Trust, OpenStack TLS, package latest |

고급 모드는 role별 `defaults/main.yml`의 `*_apply_*`, `*_enable_*`, `*_confirmed` 변수를 명시적으로 켠 경우에만 수행합니다.

원본 담당 보안 항목은 `docs/security-item-mapping.md`에서 50개 ID 기준으로 관리합니다.

| 영역 | 원본 ID 범위 | 항목 수 | 문서화 기준 |
| --- | --- | ---: | --- |
| DB | `DB-01` ~ `DB-09` | 9 | 계정, 패스워드, 권한, 파일 보호, 로그, 패치 |
| Docker | `DOCKER-01` ~ `DOCKER-20` | 20 | 패치, 그룹, user namespace, audit, no-new-privileges, service/socket/config/socket/daemon.json 권한, Content Trust, SELinux, SSH, privileged port, PIDs |
| Kubernetes | `K8S-01` ~ `K8S-05` | 5 | Control Plane, API Server, etcd, Kubelet, Pod/RBAC/NetworkPolicy/Secret |
| OpenStack 인증/인가 | `OSAUTH-01` ~ `OSAUTH-16` | 16 | Keystone/Nova/Cinder/Glance/Neutron 인증, TLS, 요청 크기, token |

`precheck`, `backup`, `validate`, `handler`, Kubernetes 노드 역할 감지, Kubernetes YAML 검증, Docker warn/fail 모드는 원본 50개를 안전하게 실행하기 위한 운영 안정성 보조 로직으로 유지합니다. Horizon, Cinder volume encryption, OpenStack 설정 파일 권한 hardening, Docker daemon 보안 옵션 병합, Neutron auth_strategy 추가 보강은 원본 50개 밖의 보안 목적 항목이므로 기본 실행에서 제외합니다.

### b. Check Mode 실행

```bash
ANSIBLE_HOME=.ansible ansible-playbook playbooks/security-policy-2026.yml \
  -i inventory/security-policy-2026.example.ini \
  --check
```

특정 role만 확인하려면 tag를 사용합니다.

```bash
ANSIBLE_HOME=.ansible ansible-playbook playbooks/security-policy-2026.yml \
  -i inventory/security-policy-2026.example.ini \
  --check \
  --tags docker
```

### c. Diff 확인

```bash
ANSIBLE_HOME=.ansible ansible-playbook playbooks/security-policy-2026.yml \
  -i inventory/security-policy-2026.example.ini \
  --check --diff
```

설정 파일 변경이 예상되는 role은 `backup: true` 또는 사전 backup task를 사용합니다. diff에서 인증서, 토큰, 비밀번호 같은 민감값이 출력될 수 있으므로 로그 보관 위치를 제한합니다.

### d. Role별 실행 방법

```bash
# 전체 보안 정책
ANSIBLE_HOME=.ansible ansible-playbook playbooks/security-policy-2026.yml \
  -i inventory/security-policy-2026.example.ini

# DB
ANSIBLE_HOME=.ansible ansible-playbook playbooks/security-policy-2026.yml \
  -i inventory/security-policy-2026.example.ini --tags db

# Docker
ANSIBLE_HOME=.ansible ansible-playbook playbooks/security-policy-2026.yml \
  -i inventory/security-policy-2026.example.ini --tags docker

# Kubernetes
ANSIBLE_HOME=.ansible ansible-playbook playbooks/security-policy-2026.yml \
  -i inventory/security-policy-2026.example.ini --tags k8s

# OpenStack 전체
ANSIBLE_HOME=.ansible ansible-playbook playbooks/openstack-security.yml \
  -i inventory/openstack.example.ini
```

OpenStack 컴포넌트별 실행은 inventory limit을 사용합니다.

```bash
ANSIBLE_HOME=.ansible ansible-playbook playbooks/openstack-security.yml \
  -i inventory/openstack.example.ini --limit keystone
```

### e. Validate 실행 방법

각 role은 기본적으로 적용 후 validate task를 실행하도록 구성되어 있습니다. validate만 다시 확인하려면 실제 적용 변수를 끄고 validate 변수를 켠 상태로 check-only 성격의 task를 실행합니다.

```bash
ANSIBLE_HOME=.ansible ansible-playbook playbooks/security-policy-2026.yml \
  -i inventory/security-policy-2026.example.ini \
  --tags docker \
  -e docker_validate_after_apply=true
```

프로젝트 수준 문법과 Molecule playbook smoke 검증은 아래 명령으로 실행합니다.

```bash
ANSIBLE_HOME=.ansible molecule test -s project-syntax
```

외부 VM 기반 Molecule verify는 대상 서버를 명시해야 합니다.

```bash
MOLECULE_TARGET_HOST=<host> \
MOLECULE_TARGET_USER=<user> \
MOLECULE_TARGET_PRIVATE_KEY_FILE=<key> \
ANSIBLE_HOME=.ansible molecule verify -s db-security
```

OpenStack delegated verify는 컴포넌트도 함께 지정합니다.

```bash
MOLECULE_TARGET_HOST=<host> \
MOLECULE_OPENSTACK_COMPONENT=keystone \
ANSIBLE_HOME=.ansible molecule verify -s openstack-component
```

### f. 위험 작업 기본 비활성 목록

| 영역 | 기본 비활성 항목 |
| --- | --- |
| DB | 패스워드 정책 강제 적용, 런타임 사용자 강제 변경, 인증 플러그인 변경, 패키지 업데이트, `general_log` 강제 활성화 |
| Docker | 패키지 업데이트, Docker restart, audit 강제 활성화, daemon.json 보안 옵션 병합, Content Trust 강제 적용, SELinux/PIDs/no-new-privileges/컨테이너 SSH/privileged port 자동 조치 |
| Kubernetes | control-plane/static pod manifest 수정, API server/etcd/kubelet 수정, kubelet restart, etcd encryption, etcd 데이터 디렉터리 권한 변경, NetworkPolicy/PSA/PSS 강제 적용, Admission Plugin 일괄 추가, audit log 강제 설정 |
| OpenStack | Keystone 및 전체 TLS 전환, OpenStack 설정 파일 권한 hardening, Neutron auth_strategy 추가 보강, Horizon role, Cinder volume encryption |

### g. 구현 제외/예외 항목

아래 항목은 운영 영향 또는 외부 선행 조건 때문에 자동 적용하지 않고 `check-only`, `manual-required`, `exception`, `out-of-scope`로 분리합니다.

- Docker SELinux 보안 옵션 설정
- Docker PIDs cgroup 제한
- Docker Content Trust 강제 활성화
- Docker no-new-privileges 일괄 적용
- 컨테이너 SSH 사용 금지
- Kubernetes NetworkPolicy 자동 적용
- Kubernetes PSA/PSS 강제 적용
- Admission Control Plugin 일괄 추가
- Cinder 볼륨 암호화 자동 구성
- Keystone 및 OpenStack 전체 TLS 자동 전환
- Horizon Secure Cookie 자동 적용
- DB `general_log` 강제 활성화
- 패키지 `latest` 자동 업데이트

### h. 실제 서버 적용 시 주의사항

- 첫 실행은 반드시 `--check --diff`로 변경 범위를 확인합니다.
- 운영 서비스 재시작 변수는 기본값이 `false`입니다. 유지보수 창에서 명시적으로 켭니다.
- Kubernetes control-plane과 etcd 변경은 백업, rollback 계획, 클러스터 quorum 확인 후 진행합니다.
- OpenStack TLS는 endpoint catalog, CA trust, 로드밸런서, 클라이언트 openrc 전환 계획이 준비된 뒤 단계적으로 적용합니다.
- DB 계정/권한 변경은 모니터링 계정, 백업 계정, 애플리케이션 계정 예외를 먼저 정리합니다.
- Docker daemon 설정 변경은 컨테이너 재시작 영향을 확인한 뒤 적용합니다.
- validate 실패는 drift 또는 선행 조건 누락을 의미하므로, 실패 task의 assert 메시지와 대상 설정 파일을 먼저 확인합니다.
