# db-security

MariaDB/MySQL 서버의 계정 정리, 권한 제한, 실행 계정, 설정 파일 권한, 로그 설정을 적용하는 Ansible Role입니다.

## 구현 task

| 파일 | 구현 내용 |
| --- | --- |
| `tasks/1_accounts_password.yml` | 익명 사용자와 테스트 계정을 제거하고, DB 설정 파일의 `[mysqld]` 섹션에 패스워드 복잡도 정책을 추가합니다. |
| `tasks/2_privileges.yml` | 일반 DB 사용자에게서 `GRANT OPTION`과 `mysql.user` 조회 권한을 회수합니다. |
| `tasks/3_root_and_logging.yml` | DB 데몬 실행 계정을 `mysql`로 제한하고, 설정 파일 권한을 `0640`으로 조정하며, Slow Query/Error 로그 설정을 추가합니다. |

## 적용이 필요한 이유

- 익명/테스트 계정은 불필요한 인증 우회 또는 약한 접근 지점이 될 수 있습니다.
- 일반 계정의 권한 위임과 계정 테이블 조회는 권한 확대와 정보 노출 위험을 키웁니다.
- DB 서버를 root로 실행하면 DB 취약점이 호스트 root 권한으로 이어질 수 있습니다.
- 설정 파일과 로그 설정은 사고 조사, 장애 분석, 비인가 변경 추적에 필요합니다.

## 적용 시 변경점

- 빈 이름의 익명 사용자와 `db_test_users`에 지정된 테스트 계정이 삭제됩니다.
- `db_config_file`에 패스워드 정책 block이 추가되고 DB 서비스가 재시작됩니다.
- `db_regular_users`에 지정된 계정의 `GRANT OPTION`, `mysql.user` SELECT 권한 회수를 시도합니다.
- DB 설정 파일의 `user` 값이 `db_runtime_user`로 설정됩니다.
- DB 설정 파일 소유권/권한이 `root:db_runtime_group`, `0640`으로 변경됩니다.
- `db_log_dir`가 생성되고 Slow Query/Error 로그 설정 block이 추가됩니다.

## 변수 설명

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `db_service_name` | `mariadb` | 재시작할 DB 서비스명입니다. |
| `db_config_file` | `/etc/my.cnf` | DB 설정 파일 경로입니다. 배포판별 실제 경로 확인이 필요합니다. |
| `db_login_unix_socket` | `/var/lib/mysql/mysql.sock` | `community.mysql` 모듈 접속에 사용할 Unix socket 경로입니다. |
| `db_runtime_user` | `mysql` | DB 데몬 실행 계정입니다. |
| `db_runtime_group` | `mysql` | DB 설정 파일과 로그 디렉터리에 사용할 그룹입니다. |
| `db_test_users` | `test`, `guest` | 제거할 테스트 계정 목록입니다. |
| `db_regular_users` | `[]` | 권한 회수 대상 일반 DB 사용자 목록입니다. 실제 계정명을 지정해야 합니다. |
| `db_password_policy_marker` | `# {mark} ANSIBLE MANAGED BLOCK - Password Policy` | 패스워드 정책 block 식별자입니다. |
| `db_logging_marker` | `# {mark} ANSIBLE MANAGED BLOCK - Logging` | 로그 설정 block 식별자입니다. |
| `db_password_policy_block` | `simple_password_check` 설정 | `[mysqld]` 섹션에 추가할 패스워드 복잡도 정책입니다. DB 버전에 맞게 플러그인명을 확인해야 합니다. |
| `db_log_dir` | `/var/log/mysql` | DB 로그 디렉터리입니다. |
| `db_slow_query_log_file` | `/var/log/mysql/mariadb-slow.log` | Slow Query 로그 파일 경로입니다. |
| `db_error_log_file` | `/var/log/mysql/error.log` | Error 로그 파일 경로입니다. |
| `db_long_query_time` | `2` | Slow Query 기준 시간(초)입니다. |
