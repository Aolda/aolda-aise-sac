# aolda-aise-sac

Ansible 기반 Security as Code 프로젝트 레포지토리입니다.

## Repository Structure

| 경로 | 설명 |
| --- | --- |
| `docs/` | Git 규칙, 아키텍처 등 프로젝트 문서 |
| `roles/docker-security/` | Docker 호스트 보안 설정 role |
| `roles/db-security/` | MariaDB/MySQL 보안 설정 role |
| `roles/k8s-security/` | Kubernetes 보안 설정 role |

## Roles

| Role | 주요 내용 |
| --- | --- |
| `docker-security` | Docker 패키지 업데이트, 그룹 사용자 제한, 감사 규칙, 파일 권한, daemon 보안 설정, 런타임 컨테이너 점검 |
| `db-security` | DB 계정 정리, 권한 제한, 패스워드 정책, 실행 계정/파일 권한/로그 설정, 인증 플러그인, 패키지 패치 |
| `k8s-security` | Control Plane/API Server/etcd/Kubelet 보안 설정, PSA 라벨 및 Pod 보안 점검 |

## Workflow

- `main`: 안정화된 기준 브랜치
- `feature/*`, `docs/*`, `chore/*` 브랜치에서 작업 후 PR로 `main`에 병합
