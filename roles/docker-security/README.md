# docker-security

Docker 호스트의 패키지, 사용자 권한, 감사 로그, 주요 파일 권한, 실행 중인 컨테이너 보안 점검을 적용하는 Ansible Role입니다. daemon 보안 옵션 병합은 원본 20개 밖 확장 기능으로 기본 실행에서 제외합니다.

## 구현 task

| 파일 | 구현 내용 |
| --- | --- |
| `tasks/1_version_and_users.yml` | 조건부로 Docker 패키지를 관리하고, Docker 그룹 생성, 허용 사용자 추가, 지정 사용자 제거, 선택적으로 `DOCKER_CONTENT_TRUST=1` 전역 환경 변수 설정을 수행합니다. |
| `tasks/2_audit_config.yml` | `docker_apply_audit_config=true`일 때 `auditd`를 설치하고 Docker 바이너리, 설정 디렉터리, systemd unit, OS별 default/sysconfig 파일 중 실제 존재하는 경로만 감사 규칙에 등록합니다. |
| `tasks/3_file_permissions.yml` | Docker systemd unit, socket, `/etc/docker` 디렉터리의 소유권과 권한을 제한합니다. |
| `tasks/4_daemon_security.yml` | 원본 20개 밖 확장 기능입니다. `docker_enable_daemon_config_extension=true`와 `docker_apply_daemon_security=true`일 때만 기존 `daemon.json`을 파싱해 `docker_daemon_config`와 병합합니다. |
| `tasks/5_container_runtime_checks.yml` | Docker CLI로 컨테이너 런타임 상태를 조회하고 host user namespace, SecurityOpt, SELinux, SSH 프로세스, privileged port, PIDs 제한을 점검합니다. |

## 적용이 필요한 이유

- Docker 그룹 권한은 사실상 root에 준하는 권한이므로 허용 계정만 포함해야 합니다.
- Docker 관련 실행 파일과 설정 파일 변경은 침해 징후가 될 수 있어 감사 로그 대상에 포함해야 합니다.
- Docker socket과 설정 파일 권한이 과도하면 일반 사용자가 컨테이너 또는 호스트 권한을 우회할 수 있습니다.
- daemon 보안 옵션 병합은 원본 DOCKER-14/15의 daemon.json 소유권/권한 항목과 분리하며, 운영 영향이 있어 확장 변수로만 적용합니다.
- 실행 중인 컨테이너의 host namespace 공유, SSH 실행, PID 제한 누락은 운영 중 권한 확대와 공격면 확대로 이어질 수 있습니다.

## 적용 시 변경점

- `docker_apply_package_update`가 `true`이면 OS 계열에 따라 Docker 패키지를 `docker_package_state` 값으로 관리합니다. 기본값은 `present`이며 `latest` 자동 업데이트는 기본 적용하지 않습니다.
- `docker` 그룹이 생성되고 `docker_allowed_users`에 지정된 사용자가 추가됩니다. `docker_disallowed_group_users`에 지정된 사용자는 `docker_groups_to_clean` 대상 그룹에서 제거됩니다.
- `docker_enable_content_trust`가 `true`이면 `/etc/profile.d/docker-security.sh`에 Docker Content Trust 환경 변수가 생성됩니다.
- `docker_apply_audit_config`가 `true`이면 `/etc/audit/rules.d/audit.rules`에 Docker 관련 경로 감사 규칙이 추가됩니다. `auditd` 재시작은 `docker_restart_auditd`로 별도 제어합니다.
- Docker unit/socket/config 경로의 권한이 role 변수 기준으로 조정됩니다.
- `docker_enable_daemon_config_extension`과 `docker_apply_daemon_security`가 모두 `true`이면 `/etc/docker/daemon.json`이 기존 JSON과 `docker_daemon_config`의 병합 결과로 생성 또는 갱신됩니다. Docker 서비스 재시작은 `docker_restart_service`로 별도 제어합니다.
- `docker_enable_runtime_container_checks`가 `true`이면 컨테이너 런타임 보안 상태를 점검합니다. 기본값은 경고 출력이며, `docker_fail_on_runtime_policy_violation`을 `true`로 설정하면 일부 위반을 실패 처리합니다.

## 변수 설명

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `docker_service_name` | `docker` | 재시작할 Docker 서비스명입니다. |
| `docker_group_name` | `docker` | Docker 명령 실행 권한을 부여할 그룹명입니다. |
| `docker_package_name_debian` | `docker-ce` | Debian/Ubuntu 계열 Docker 패키지명입니다. |
| `docker_package_name_redhat` | `docker-ce` | RHEL/CentOS 계열 Docker 패키지명입니다. |
| `docker_package_state` | `present` | 패키지 적용 상태입니다. `latest`는 명시적으로 선택한 경우에만 사용합니다. |
| `docker_apply_package_update` | `false` | Docker 패키지 최신 업데이트 적용 여부입니다. 운영 영향이 있어 기본 비활성입니다. |
| `docker_apply_daemon_security` | `false` | Docker daemon 보안 설정 적용 여부입니다. 기존 컨테이너/볼륨 영향이 있어 기본 비활성입니다. |
| `docker_enable_daemon_config_extension` | `false` | 원본 20개 밖의 daemon.json 보안 옵션 병합 확장 기능 포함 여부입니다. 기본 실행에서 제외합니다. |
| `docker_apply_audit_config` | `false` | Docker audit 규칙 적용 여부입니다. 로그 정책과 auditd 재시작 영향이 있어 기본 비활성입니다. |
| `docker_validate_after_apply` | `true` | 적용 후 validate task 실행 여부입니다. |
| `docker_restart_service` | `false` | daemon 설정 변경 후 Docker 서비스를 재시작할지 여부입니다. 운영 영향이 있어 기본 비활성입니다. |
| `docker_restart_auditd` | `false` | audit rule 변경 후 auditd를 재시작할지 여부입니다. 운영 영향이 있어 기본 비활성입니다. |
| `auditd_package_name` | `audit` | 감사 로그 패키지명입니다. |
| `auditd_service_name` | `auditd` | 감사 로그 서비스명입니다. |
| `audit_rules_file` | `/etc/audit/rules.d/audit.rules` | 감사 규칙을 추가할 파일입니다. |
| `docker_allowed_users` | `[root]` | Docker 그룹에 추가할 허용 사용자 목록입니다. `root`는 별도 추가하지 않습니다. |
| `docker_disallowed_group_users` | `[]` | Docker 관련 그룹에서 제거할 사용자 목록입니다. |
| `docker_groups_to_clean` | `[docker_group_name]` | `docker_disallowed_group_users`를 제거할 그룹 목록입니다. |
| `docker_content_trust_profile` | `/etc/profile.d/docker-security.sh` | Content Trust 환경 변수를 기록할 profile 파일 경로입니다. |
| `docker_enable_content_trust` | `false` | Docker Content Trust profile 생성 여부입니다. 사용자 shell/CI 환경까지 강제할 수 없어 기본 비활성입니다. |
| `docker_config_dir` | `/etc/docker` | Docker 설정 디렉터리입니다. |
| `docker_daemon_config_path` | `/etc/docker/daemon.json` | Docker daemon 설정 파일 경로입니다. |
| `docker_socket_path` | `/var/run/docker.sock` | Docker socket 파일 경로입니다. |
| `docker_service_unit_path` | `/lib/systemd/system/docker.service` | Docker service unit 경로입니다. OS별 실제 경로 확인이 필요합니다. |
| `docker_socket_unit_path` | `/lib/systemd/system/docker.socket` | Docker socket unit 경로입니다. OS별 실제 경로 확인이 필요합니다. |
| `docker_audit_watch_paths` | 목록 | 감사 대상으로 등록할 Docker 관련 경로 목록입니다. 실제 존재하는 경로만 등록됩니다. |
| `docker_daemon_config` | `{}` | `daemon.json`에 병합할 보안 설정입니다. 기본값은 빈 dict라 daemon 설정을 변경하지 않습니다. |
| `docker_enable_runtime_container_checks` | `true` | 컨테이너 런타임 보안 점검 실행 여부입니다. |
| `docker_runtime_check_mode` | `warn` | 런타임 정책 위반 처리 방식입니다. `warn`은 경고만 출력하고 `fail`은 실패 처리합니다. |
| `docker_fail_on_runtime_policy_violation` | `false` | 런타임 정책 위반을 role 실패로 처리할지 여부입니다. |
| `docker_forbidden_container_process_patterns` | `sshd`, `/usr/sbin/sshd` | 컨테이너 프로세스 목록에서 금지할 문자열 패턴입니다. |
| `docker_privileged_port_threshold` | `1024` | privileged port 경고 기준 포트 번호입니다. |
| `docker_required_container_security_opts` | `no-new-privileges:true` | 컨테이너 HostConfig에 필요한 SecurityOpt 목록입니다. |
