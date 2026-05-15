# os_security

## 적용 대상

* OS (Ubuntu)

## 구현 task

*   **계정 및 인증 통제 (`account.yml`)**
    *   SSH 설정(`sshd_config`)에서 root 계정 원격 접속 제한
    *   `login.defs` 파일 수정을 통한 패스워드 최대 사용 기간 설정 (90일)
    *   `pam_pwquality.so` 모듈을 이용한 패스워드 복잡도(최소 길이, 대/소문자, 숫자, 특수문자 조합) 정책 강제
    *   `pam_tally2.so` 모듈을 통한 로그인 실패 시 계정 잠금 임계값 및 해제 시간 설정
*   **주요 설정 파일 및 디렉터리 권한 통제 (`file.yml`)**
    *   `/etc/passwd`, `/etc/hosts`, `/etc/services`, `/etc/profile` 및 사용자 홈 디렉터리 환경 파일 권한 `644`로 제한
    *   `/etc/shadow` 파일 권한 `400`으로 제한
    *   TCP Wrapper 설정을 위해 `/etc/hosts.deny`에 모든 접근 차단(`ALL: ALL`) 설정 후, `/etc/hosts.allow`에 허가된 IP 목록 추가
    *   인증 우회 파일인 `/etc/hosts.equiv` 및 `.rhosts` 파일 일괄 제거
    *   World-writable 파일(타 사용자 쓰기 권한 부여 파일) 검색 및 쓰기 권한(`o-w`) 제거
    *   권한 상승에 악용될 수 있는 주요 실행 파일 목록의 SUID/SGID 속성 제거(`chmod -s`)
    *   root 홈 디렉터리 타 사용자 접근 제한 (`700` 권한)
    *   소유자나 그룹이 없는 고아(Orphan) 파일의 소유권을 root로 일괄 변경
    *   `/etc/profile` 및 사용자 환경 파일의 PATH 변수 내에 위치한 현재 디렉터리(`.` 또는 `::`) 일괄 제거
*   **불필요한 서비스 및 데몬 통제 (`service.yml`)**
    *   불필요하고 취약한 레거시 패키지(`finger`, `talk`, `rsh` 등) 완전 제거
    *   xinetd 기반 취약 서비스(`echo`, `rlogin`, `tftp` 등) 구성 파일에서 `disable = yes`로 비활성화
    *   독립 데몬(`nfs-server`, `rpcbind` 등) 중지 및 수동으로도 켜지지 않도록 마스킹(`masked: yes`) 처리
    *   `vsftpd` 및 `proftpd` 환경 파일 수정을 통한 Anonymous FTP 익명 접속 차단
*   **시스템 유지보수 및 인프라 운영 (`system.yml`)**
    *   불필요한 NTP 데몬(`ntp`, `chrony`) 패키지 제거 및 `systemd-timesyncd` 설치·활성화
    *   시스템 시간대(Timezone) 설정 및 `/etc/localtime`, `/etc/timezone`, `timesyncd.conf` 파일 권한 `644` 보호
    *   `/etc/rsyslog.conf` 로그 설정 파일 권한 `644` 설정
    *   스케줄러 보안을 위한 `/etc/crontab` 권한 `640` 설정 및 화이트리스트용 `/etc/cron.allow` 생성
    *   cron 관련 주요 디렉터리(`/etc/cron.hourly` 등)의 타 사용자 쓰기 권한(`o-w`) 일괄 제거
    *   OS 및 패키지의 최신 보안 패치 적용(`apt upgrade: dist`)

## 해당 task 적용이 필요한 이유

*   **계정 및 인증 통제**: 비인가자의 무차별 대입 공격(Brute-force) 난이도를 대폭 높이고, 시스템의 최고 권한인 root 계정이 외부에서 탈취되어 즉각적으로 전체 시스템이 장악되는 치명적인 위험을 방지하기 위함입니다.
*   **파일 및 권한 통제**: 인가되지 않은 일반 사용자가 주요 시스템 설정이나 환경 변수를 변조하는 것을 막습니다. 특히 SUID/SGID 속성이나 PATH 변수 내 `.`을 악용한 권한 상승 및 악성코드(백도어) 위장 실행 공격을 원천적으로 차단합니다.
*   **서비스 통제**: 암호화되지 않은 원격 접속, 익명 파일 업로드/다운로드, DOS 증폭 공격에 악용될 수 있는 불필요한 네트워크 포트를 닫아 해커의 시스템 침투 표면(Attack Surface)을 최소화합니다.
*   **시스템 관리**: 시스템 로그의 타임라인을 정확히 일치시켜 추후 침해 사고 시 명확한 분석이 가능하게 하며, 비인가자가 악의적인 스케줄러(cron)를 등록하여 백도어를 유지하는 것을 차단합니다. 또한, 최신 보안 패치를 통해 알려진 취약점을 사전에 예방합니다.

## 해당 task 적용시 변경점

*   **설정 파일 및 데몬 재시작**: `sshd_config`, `xinetd`, `timesyncd`, `rsyslog` 설정이 변경됨에 따라 각각의 서비스 데몬이 안전하게 재시작(handlers 호출)되어 새로운 정책이 즉시 반영됩니다.
*   **접근 권한의 획기적 강화**: `/etc/shadow` 권한이 `400`으로 조율되어 타 사용자의 읽기가 원천 거부되며, TCP Wrapper 적용으로 `hosts.deny`에 막혀 등록된 관리자 IP 외의 모든 외부 SSH 접근이 끊어집니다.
*   **서비스 및 파일 삭제**: 시스템에 존재하던 취약한 패키지(`rsh-server`, `nfs-server` 등) 및 인증 우회 파일(`.rhosts`, `hosts.equiv`)이 시스템상에서 완전히 삭제(Absent)됩니다.
*   **계정 잠금 적용**: 패스워드를 5회 연속 잘못 입력하면 즉시 해당 계정이 600초간 잠기도록 PAM 모듈이 동작합니다.
*   **스케줄러 제어**: 모든 cron 디렉터리의 쓰기 권한이 통제되며, 새롭게 생성된 `/etc/cron.allow` 파일을 통해 명시된 사용자만 예약 작업을 등록할 수 있도록 정책이 화이트리스트 방식으로 전환됩니다.

## 변수 설명 (`defaults/main.yaml`)

코드 내에 하드코딩을 방지하고 유연한 보안 정책 관리를 위해 정의된 변수 목록은 다음과 같습니다.

### [계정 및 패스워드 정책 변수]
*   `sshd_permit_root_login`: SSH root 원격 로그인 허용 여부 (기본값: 'no')
*   `os_pass_max_days`: 패스워드 최대 사용 유효 기간 (기본값: 90)
*   `pam_pwquality_retry`: 패스워드 변경 시 최대 재시도 횟수 (기본값: 3)
*   `pam_pwquality_minlen`: 패스워드 최소 길이 요구사항 (기본값: 8)
*   `pam_pwquality_lcredit`, `ucredit`, `dcredit`, `ocredit`: 각각 소문자, 대문자, 숫자, 특수문자의 최소 요구 개수 (기본값: -1로 필수 포함)
*   `pam_deny_count`: 계정 잠금이 발생하는 로그인 실패 허용 횟수 (기본값: 5)
*   `pam_unlock_time`: 로그인 실패로 계정 잠금 시 유지되는 시간(초) (기본값: 600)

### [파일 및 접근 제어 정책 변수]
*   `file_owner_root`, `file_group_root`: 파일의 소유자 및 그룹을 지정할 변수 (기본값: 'root')
*   `file_mode_644`: 일반 설정 파일의 소유자 외 쓰기 방지 권한 (기본값: '0644')
*   `file_mode_640`: 스케줄러 등 제한된 설정 파일 권한 (기본값: '0640')
*   `file_mode_400`: 암호 해시 등 민감 파일의 관리자 전용 권한 (기본값: '0400')
*   `dir_mode_700`: 중요 디렉터리의 타 사용자 접근 원천 차단 권한 (기본값: '0700')
*   `allowed_ssh_ips`: TCP Wrapper(`/etc/hosts.allow`)를 통해 접속을 허용할 관리자 IP 및 대역 리스트
*   `unnecessary_suid_sgid_files`: 권한 상승 공격 방지를 위해 SUID/SGID 속성을 제거할 취약 파일 리스트 (`/sbin/dump`, `/usr/bin/at` 등)

### [서비스 통제 정책 변수]
*   `unnecessary_packages`: 시스템에서 완전히 제거할 취약/레거시 패키지 리스트 (`finger`, `rsh-server`, `autofs` 등)
*   `xinetd_vulnerable_services`: `disable = yes`로 설정할 xinetd 기반 서비스 리스트 (`echo`, `rlogin`, `tftp` 등)
*   `standalone_services_to_disable`: 중지 및 마스킹 처리할 독립 데몬 서비스 리스트 (`nfs-server`, `rpcbind` 등)

### [시스템 환경 및 경로 변수]
*   `system_timezone`: 시스템 로그 기준이 될 시간대 (기본값: 'Asia/Seoul')
*   `apply_security_updates`: OS 최신 보안 패치 자동 적용 여부 (기본값: yes)
*   `cron_directories`: 타 사용자 쓰기 권한을 제한할 스케줄러 관련 주요 폴더 리스트
*   `path_sshd_config`, `path_passwd`, `path_rsyslog_conf` 등: 조치 대상이 되는 시스템 주요 설정 파일의 절대 경로 변수 목록