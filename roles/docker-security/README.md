# docker-security

Docker 호스트의 패키지, 사용자 권한, 감사 로그, 주요 파일 권한, daemon 보안 설정을 적용하는 Ansible Role입니다.

## 구현 task

| 파일 | 구현 내용 |
| --- | --- |
| `tasks/1_version_and_users.yml` | Docker 패키지를 최신 상태로 갱신하고, Docker 그룹 및 허용 사용자만 그룹에 포함하며, `DOCKER_CONTENT_TRUST=1` 전역 환경 변수를 설정합니다. |
| `tasks/2_audit_config.yml` | `auditd`를 설치하고 Docker 바이너리, 설정 디렉터리, systemd unit, OS별 default/sysconfig 파일 중 실제 존재하는 경로만 감사 규칙에 등록합니다. |
| `tasks/3_file_permissions.yml` | Docker systemd unit, socket, `/etc/docker` 디렉터리의 소유권과 권한을 제한합니다. |
| `tasks/4_daemon_security.yml` | `daemon.json`에 컨테이너 권한 상승 제한, user namespace remap, SELinux, PID 제한 설정을 적용합니다. |

## 적용이 필요한 이유

- Docker 그룹 권한은 사실상 root에 준하는 권한이므로 허용 계정만 포함해야 합니다.
- Docker 관련 실행 파일과 설정 파일 변경은 침해 징후가 될 수 있어 감사 로그 대상에 포함해야 합니다.
- Docker socket과 설정 파일 권한이 과도하면 일반 사용자가 컨테이너 또는 호스트 권한을 우회할 수 있습니다.
- daemon 보안 옵션은 컨테이너 내부 권한 상승과 과도한 프로세스 생성을 줄입니다.

## 적용 시 변경점

- OS 계열에 따라 `docker-ce` 패키지가 최신 상태로 갱신됩니다.
- `docker` 그룹이 생성되고 `docker_allowed_users`에 지정된 사용자만 추가됩니다.
- `/etc/profile.d/docker-security.sh`에 Docker Content Trust 환경 변수가 생성됩니다.
- `/etc/audit/rules.d/audit.rules`에 Docker 관련 경로 감사 규칙이 추가되고 `auditd`가 재시작됩니다.
- Docker unit/socket/config 경로의 권한이 role 변수 기준으로 조정됩니다.
- `/etc/docker/daemon.json`이 `docker_daemon_config` 값으로 생성 또는 덮어쓰기되며 Docker 서비스가 재시작됩니다.

## 변수 설명

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `docker_service_name` | `docker` | 재시작할 Docker 서비스명입니다. |
| `docker_group_name` | `docker` | Docker 명령 실행 권한을 부여할 그룹명입니다. |
| `docker_package_name_debian` | `docker-ce` | Debian/Ubuntu 계열 Docker 패키지명입니다. |
| `docker_package_name_redhat` | `docker-ce` | RHEL/CentOS 계열 Docker 패키지명입니다. |
| `auditd_package_name` | `audit` | 감사 로그 패키지명입니다. |
| `auditd_service_name` | `auditd` | 감사 로그 서비스명입니다. |
| `audit_rules_file` | `/etc/audit/rules.d/audit.rules` | 감사 규칙을 추가할 파일입니다. |
| `docker_allowed_users` | `[root]` | Docker 그룹에 추가할 허용 사용자 목록입니다. `root`는 별도 추가하지 않습니다. |
| `docker_content_trust_profile` | `/etc/profile.d/docker-security.sh` | Content Trust 환경 변수를 기록할 profile 파일 경로입니다. |
| `docker_enable_content_trust` | `true` | Docker Content Trust 설정 적용 여부입니다. |
| `docker_config_dir` | `/etc/docker` | Docker 설정 디렉터리입니다. |
| `docker_daemon_config_path` | `/etc/docker/daemon.json` | Docker daemon 설정 파일 경로입니다. |
| `docker_socket_path` | `/var/run/docker.sock` | Docker socket 파일 경로입니다. |
| `docker_service_unit_path` | `/lib/systemd/system/docker.service` | Docker service unit 경로입니다. OS별 실제 경로 확인이 필요합니다. |
| `docker_socket_unit_path` | `/lib/systemd/system/docker.socket` | Docker socket unit 경로입니다. OS별 실제 경로 확인이 필요합니다. |
| `docker_audit_watch_paths` | 목록 | 감사 대상으로 등록할 Docker 관련 경로 목록입니다. 실제 존재하는 경로만 등록됩니다. |
| `docker_daemon_config` | dict | `daemon.json`에 적용할 보안 설정입니다. 기존 설정이 있으면 병합 값을 변수에 반영해야 합니다. |
