# db-security

MariaDB/MySQL 서버의 계정 정리, 권한 제한, 패스워드 정책, 실행 계정, 설정 파일 권한, 로그 설정, 인증 플러그인, 패키지 패치를 적용하는 Ansible Role입니다.

## 구현 task

| 파일 | 구현 내용 |
| --- | --- |
| `tasks/1_accounts_password.yml` | 익명 사용자와 테스트 계정을 제거하고, DB 설정 파일의 `[mysqld]` 섹션에 패스워드 복잡도 정책을 추가합니다. |
| `tasks/2_privileges.yml` | 일반 DB 사용자에게서 `GRANT OPTION`과 `mysql.user` 조회 권한을 회수합니다. |
| `tasks/3_root_and_logging.yml` | DB 데몬 실행 계정을 `mysql`로 제한하고, 설정 파일 권한을 `0640`으로 조정하며, Slow Query/Error 로그 설정을 추가합니다. |
| `tasks/4_authentication_and_patch.yml` | 기본/사용자별 인증 플러그인을 설정하고, 조건부로 DB 패키지 보안 패치를 적용한 뒤 DB 버전을 출력합니다. |

## 적용이 필요한 이유

- 익명/테스트 계정은 불필요한 인증 우회 또는 약한 접근 지점이 될 수 있습니다.
- 일반 계정의 권한 위임과 계정 테이블 조회는 권한 확대와 정보 노출 위험을 키웁니다.
- DB 서버를 root로 실행하면 DB 취약점이 호스트 root 권한으로 이어질 수 있습니다.
- 설정 파일과 로그 설정은 사고 조사, 장애 분석, 비인가 변경 추적에 필요합니다.
- 취약하거나 오래된 인증 플러그인과 미패치 DB 패키지는 인증 우회, 취약점 악용 위험을 키울 수 있습니다.

## 적용 시 변경점

- 빈 이름의 익명 사용자, `db_test_users`에 지정된 테스트 계정, `db_unnecessary_accounts`와 `db_disallowed_account_hosts`에 지정된 계정이 삭제됩니다.
- `db_config_file`에 MariaDB `simple_password_check` 또는 MySQL `validate_password` 정책 block이 조건에 따라 추가되고 DB 서비스가 재시작됩니다.
- `db_enable_validate_password_component`가 `true`이면 MySQL `component_validate_password` 설치를 시도합니다.
- `db_regular_users`에 지정된 계정의 `GRANT OPTION`, `mysql.user` SELECT 권한 회수를 시도합니다.
- DB 설정 파일의 `user` 값이 `db_runtime_user`로 설정됩니다.
- DB 설정 파일 소유권/권한이 `root:db_runtime_group`, `0640`으로 변경됩니다.
- `db_log_dir`가 생성되고 Slow Query/Error 로그 설정 block이 추가됩니다. `db_enable_general_log`가 `true`이면 General Log 설정도 함께 추가됩니다.
- `db_set_default_authentication_plugin`이 `true`이면 기본 인증 플러그인 설정이 추가됩니다.
- `db_secure_auth_users`에 지정된 계정의 인증 플러그인을 변경합니다.
- `db_apply_security_patch`가 `true`이면 OS 계열에 따라 DB 패키지를 최신 상태로 갱신합니다.
- DB 버전을 조회해 출력합니다.

## 변수 설명

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `db_service_name` | `mariadb` | 재시작할 DB 서비스명입니다. |
| `db_package_name_debian` | `mariadb-server` | Debian/Ubuntu 계열 DB 패키지명입니다. |
| `db_package_name_redhat` | `mariadb-server` | RHEL/CentOS 계열 DB 패키지명입니다. |
| `db_apply_security_patch` | `false` | DB 패키지 최신 보안 패치 적용 여부입니다. |
| `db_config_file` | `/etc/my.cnf` | DB 설정 파일 경로입니다. 배포판별 실제 경로 확인이 필요합니다. |
| `db_login_unix_socket` | `/var/lib/mysql/mysql.sock` | `ansible.mysql` 모듈 접속에 사용할 Unix socket 경로입니다. |
| `db_runtime_user` | `mysql` | DB 데몬 실행 계정입니다. |
| `db_runtime_group` | `mysql` | DB 설정 파일과 로그 디렉터리에 사용할 그룹입니다. |
| `db_test_users` | `test`, `guest` | 제거할 테스트 계정 목록입니다. |
| `db_unnecessary_accounts` | `[]` | 제거할 불필요한 DB 계정 목록입니다. 각 항목에 `name`을 지정하고, 필요하면 `host`를 함께 지정합니다. |
| `db_disallowed_account_hosts` | `[]` | 허용되지 않은 host 조합으로 제거할 DB 계정 목록입니다. `name`과 `host`를 지정합니다. |
| `db_regular_users` | `[]` | 권한 회수 대상 일반 DB 사용자 목록입니다. 문자열 계정명 또는 `name`/`host` mapping을 사용할 수 있습니다. |
| `db_password_policy_marker` | `# {mark} ANSIBLE MANAGED BLOCK - Password Policy` | 패스워드 정책 block 식별자입니다. |
| `db_validate_password_marker` | `# {mark} ANSIBLE MANAGED BLOCK - Validate Password Policy` | MySQL validate_password 정책 block 식별자입니다. |
| `db_logging_marker` | `# {mark} ANSIBLE MANAGED BLOCK - Logging` | 로그 설정 block 식별자입니다. |
| `db_authentication_marker` | `# {mark} ANSIBLE MANAGED BLOCK - Authentication Plugin` | 인증 플러그인 설정 block 식별자입니다. |
| `db_password_policy_type` | `mariadb_simple` | 적용할 패스워드 정책 유형입니다. `mariadb_simple` 또는 `mysql_validate`를 사용합니다. |
| `db_enable_validate_password_component` | `false` | MySQL validate_password 컴포넌트 설치 여부입니다. |
| `db_password_policy_block` | `simple_password_check` 설정 | MariaDB `[mysqld]` 섹션에 추가할 패스워드 복잡도 정책입니다. DB 버전에 맞게 플러그인명을 확인해야 합니다. |
| `db_validate_password_block` | `validate_password` 설정 | MySQL `[mysqld]` 섹션에 추가할 validate_password 정책입니다. |
| `db_log_dir` | `/var/log/mysql` | DB 로그 디렉터리입니다. |
| `db_slow_query_log_file` | `/var/log/mysql/mariadb-slow.log` | Slow Query 로그 파일 경로입니다. |
| `db_error_log_file` | `/var/log/mysql/error.log` | Error 로그 파일 경로입니다. |
| `db_long_query_time` | `2` | Slow Query 기준 시간(초)입니다. |
| `db_enable_general_log` | `false` | General Log 설정 추가 여부입니다. |
| `db_general_log_file` | `/var/log/mysql/general.log` | General Log 파일 경로입니다. |
| `db_secure_authentication_plugin` | `caching_sha2_password` | 기본 또는 사용자별로 적용할 안전한 인증 플러그인입니다. |
| `db_set_default_authentication_plugin` | `false` | `[mysqld]`에 기본 인증 플러그인 설정을 추가할지 여부입니다. |
| `db_secure_auth_users` | `[]` | 인증 플러그인을 변경할 사용자 목록입니다. 각 항목에 `name`, `password`, 선택적으로 `host`, `plugin`을 지정합니다. |
| `db_user_table_revoke_privileges` | `ALL PRIVILEGES` | `mysql.user` 테이블에서 회수할 권한입니다. |
