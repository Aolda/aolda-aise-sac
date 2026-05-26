# docker-security

Docker 호스트의 패키지, 사용자 권한, 감사 로그, 주요 파일 권한, daemon 보안 설정, 실행 중인 컨테이너 보안 점검을 적용하는 Ansible Role입니다.

## 구현 task

| 파일 | 구현 내용 |
| --- | --- |
| `tasks/1_version_and_users.yml` | 조건부로 Docker 패키지를 최신 상태로 갱신하고, Docker 그룹 생성, 허용 사용자 추가, 지정 사용자 제거, `DOCKER_CONTENT_TRUST=1` 전역 환경 변수 설정을 수행합니다. |
| `tasks/2_audit_config.yml` | `auditd`를 설치하고 Docker 바이너리, 설정 디렉터리, systemd unit, OS별 default/sysconfig 파일 중 실제 존재하는 경로만 감사 규칙에 등록합니다. |
| `tasks/3_file_permissions.yml` | Docker systemd unit, socket, `/etc/docker` 디렉터리의 소유권과 권한을 제한합니다. |
| `tasks/4_daemon_security.yml` | 조건부로 `daemon.json`에 컨테이너 권한 상승 제한, user namespace remap, SELinux, PID 제한 설정을 적용합니다. |
| `tasks/5_container_runtime_checks.yml` | Docker CLI로 컨테이너 런타임 상태를 조회하고 host user namespace, SecurityOpt, SELinux, SSH 프로세스, privileged port, PIDs 제한을 점검합니다. |

## 적용이 필요한 이유

- Docker 그룹 권한은 사실상 root에 준하는 권한이므로 허용 계정만 포함해야 합니다.
- Docker 관련 실행 파일과 설정 파일 변경은 침해 징후가 될 수 있어 감사 로그 대상에 포함해야 합니다.
- Docker socket과 설정 파일 권한이 과도하면 일반 사용자가 컨테이너 또는 호스트 권한을 우회할 수 있습니다.
- daemon 보안 옵션은 컨테이너 내부 권한 상승과 과도한 프로세스 생성을 줄입니다.
- 실행 중인 컨테이너의 host namespace 공유, SSH 실행, PID 제한 누락은 운영 중 권한 확대와 공격면 확대로 이어질 수 있습니다.

## 적용 시 변경점

- `docker_apply_package_update`가 `true`이면 OS 계열에 따라 `docker-ce` 패키지가 최신 상태로 갱신됩니다.
- `docker` 그룹이 생성되고 `docker_allowed_users`에 지정된 사용자가 추가됩니다. `docker_disallowed_group_users`에 지정된 사용자는 `docker_groups_to_clean` 대상 그룹에서 제거됩니다.
- `/etc/profile.d/docker-security.sh`에 Docker Content Trust 환경 변수가 생성됩니다.
- `/etc/audit/rules.d/audit.rules`에 Docker 관련 경로 감사 규칙이 추가되고 `auditd`가 재시작됩니다.
- Docker unit/socket/config 경로의 권한이 role 변수 기준으로 조정됩니다.
- `docker_apply_daemon_security`가 `true`이면 `/etc/docker/daemon.json`이 `docker_daemon_config` 값으로 생성 또는 덮어쓰기되며 Docker 서비스가 재시작됩니다.
- `docker_enable_runtime_container_checks`가 `true`이면 컨테이너 런타임 보안 상태를 점검합니다. 기본값은 경고 출력이며, `docker_fail_on_runtime_policy_violation`을 `true`로 설정하면 일부 위반을 실패 처리합니다.

## 변수 설명

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `docker_service_name` | `docker` | 재시작할 Docker 서비스명입니다. |
| `docker_group_name` | `docker` | Docker 명령 실행 권한을 부여할 그룹명입니다. |
| `docker_package_name_debian` | `docker-ce` | Debian/Ubuntu 계열 Docker 패키지명입니다. |
| `docker_package_name_redhat` | `docker-ce` | RHEL/CentOS 계열 Docker 패키지명입니다. |
| `docker_apply_package_update` | `false` | Docker 패키지 최신 업데이트 적용 여부입니다. 운영 영향이 있어 기본 비활성입니다. |
| `docker_apply_daemon_security` | `false` | Docker daemon 보안 설정 적용 여부입니다. 기존 컨테이너/볼륨 영향이 있어 기본 비활성입니다. |
| `docker_apply_audit_config` | `true` | Docker audit 규칙 적용 여부입니다. 컨테이너 기반 Molecule 테스트에서는 보통 `false`로 둡니다. |
| `auditd_package_name` | `audit` | 감사 로그 패키지명입니다. |
| `auditd_service_name` | `auditd` | 감사 로그 서비스명입니다. |
| `audit_rules_file` | `/etc/audit/rules.d/audit.rules` | 감사 규칙을 추가할 파일입니다. |
| `docker_allowed_users` | `[root]` | Docker 그룹에 추가할 허용 사용자 목록입니다. `root`는 별도 추가하지 않습니다. |
| `docker_disallowed_group_users` | `[]` | Docker 관련 그룹에서 제거할 사용자 목록입니다. |
| `docker_groups_to_clean` | `[docker_group_name]` | `docker_disallowed_group_users`를 제거할 그룹 목록입니다. |
| `docker_content_trust_profile` | `/etc/profile.d/docker-security.sh` | Content Trust 환경 변수를 기록할 profile 파일 경로입니다. |
| `docker_enable_content_trust` | `true` | Docker Content Trust 설정 적용 여부입니다. |
| `docker_config_dir` | `/etc/docker` | Docker 설정 디렉터리입니다. |
| `docker_daemon_config_path` | `/etc/docker/daemon.json` | Docker daemon 설정 파일 경로입니다. |
| `docker_socket_path` | `/var/run/docker.sock` | Docker socket 파일 경로입니다. |
| `docker_service_unit_path` | `/lib/systemd/system/docker.service` | Docker service unit 경로입니다. OS별 실제 경로 확인이 필요합니다. |
| `docker_socket_unit_path` | `/lib/systemd/system/docker.socket` | Docker socket unit 경로입니다. OS별 실제 경로 확인이 필요합니다. |
| `docker_audit_watch_paths` | 목록 | 감사 대상으로 등록할 Docker 관련 경로 목록입니다. 실제 존재하는 경로만 등록됩니다. |
| `docker_daemon_config` | dict | `daemon.json`에 적용할 보안 설정입니다. 기존 설정이 있으면 병합 값을 변수에 반영해야 합니다. |
| `docker_enable_runtime_container_checks` | `true` | 컨테이너 런타임 보안 점검 실행 여부입니다. |
| `docker_fail_on_runtime_policy_violation` | `false` | 런타임 정책 위반을 role 실패로 처리할지 여부입니다. |
| `docker_forbidden_container_process_patterns` | `sshd`, `/usr/sbin/sshd` | 컨테이너 프로세스 목록에서 금지할 문자열 패턴입니다. |
| `docker_privileged_port_threshold` | `1024` | privileged port 경고 기준 포트 번호입니다. |
| `docker_required_container_security_opts` | `no-new-privileges:true` | 컨테이너 HostConfig에 필요한 SecurityOpt 목록입니다. |
