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

AISE는 Docker, DB, Kubernetes, OpenStack 등 인프라 구성 요소의 보안 설정을 Ansible role과 playbook으로 자동화합니다.

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
| `docker-security` | Docker 패키지 업데이트, 그룹 사용자 제한, 감사 규칙, 파일 권한, daemon 보안 설정, 런타임 컨테이너 점검 |
| `db-security` | DB 계정 정리, 권한 제한, 패스워드 정책, 실행 계정/파일 권한/로그 설정, 인증 플러그인, 패키지 패치 |
| `k8s-security` | Control Plane/API Server/etcd/Kubelet 보안 설정, PSA 라벨 및 Pod 보안 점검 |
| `keystone-security` | Keystone 인증, token, 파일 권한, 검증 task |
| `nova-security` | Nova 설정 파일 보안 옵션 및 검증 task |
| `neutron-security` | Neutron 설정 파일 보안 옵션 및 검증 task |
| `glance-security` | Glance 설정 파일 보안 옵션 및 검증 task |
| `cinder-security` | Cinder 설정 파일 및 volume encryption 보안 옵션 |
| `horizon-security` | Horizon SSL, cookie, password validator 보안 옵션 |

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
