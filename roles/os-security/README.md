# os-security

KISA 주요정보통신기반시설 기술적 취약점 분석·평가 가이드라인과 CIS Benchmark(Ubuntu)를 준수하여 우분투 서버의 계정 보안, 파일 권한 통제, 불필요 서비스 제거, 인프라 시간 무결성을 자동 적용하는 Ansible Role입니다. 특히 Ubuntu 고유의 인증 아키텍처(PAM)와의 호환성을 고려하여 인증 사슬(Stack) 붕괴를 원천 차단하도록 설계되었습니다.

## 구현 task

| 파일 | 구현 내용 |
| --- | --- |
| `tasks/account.yml` | OpenSSH 서버 및 필수 인증 모듈(`libpam-pwquality`)을 설치하고, root 원격 접속 제한, 패스워드 만료 주기(90일) 및 복잡도 규정을 적용합니다. 로그인 실패 시 계정 잠금(`pam_faillock`) 정책은 Ubuntu 표준 프레임워크(`pam-auth-update`)를 통해 안전하게 강제합니다. |
| `tasks/file.yml` | 주요 설정 파일 권한(passwd, shadow 등)을 Ubuntu 권한 분리 메커니즘에 맞게 조율하고, TCP Wrapper 기반 접근 통제, SUID/SGID 속성 제거, 고아 파일 귀속, PATH 변수 내 위험 요소(`.`) 제거를 수행합니다. |
| `tasks/service.yml` | 시스템 내 취약·레거시 패키지를 흔적 없이 완전 삭제(`purge`)하고, xinetd 및 독립형 불필요 데몬 중지/마스킹 처리를 수행하며 Anonymous FTP 접속을 차단합니다. |
| `tasks/system.yml` | 불필요 NTP 데몬 박멸 후 `systemd-timesyncd`를 통한 자동 동기화를 활성화하며, rsyslog 및 스케줄러(cron) 권한 방어 및 최신 보안 패치를 일괄 적용합니다. |

## 적용이 필요한 이유

* 무차별 대입 공격(Brute-force) 시 권한이 없는 격리 영역을 강제하고 외부 root 직접 로그인을 차단하여 시스템의 즉각적인 장악 위험을 차단합니다.
* 인가되지 않은 일반 사용자가 주요 시스템 설정을 변조하는 것을 막고, SUID 속성이나 PATH 변수의 취약점을 이용한 로컬 권한 상승(Privilege Escalation) 공격을 예방합니다.
* 암호화되지 않은 구형 프로토콜 및 비인가 공유 서비스를 제거하여 공격자가 침투할 수 있는 표면(Attack Surface)을 최소화합니다.
* 서버간 타임라인 동기화를 보장하여 사고 조사 시 로그 무결성을 확보하고, 악의적인 지속성 백도어로 악용될 수 있는 스케줄러(cron)의 임의 등록을 통제합니다.

## 적용 시 변경점

* 미니멀 환경 대비 `package_netbase`, `package_ssh_server`, 패스워드 복잡도 검증을 위한 `libpam-pwquality` 패키지가 사전 점검 후 설치되며, 격리용 `path_sshd_run_dir` 디렉터리가 생성됩니다.
* 로그인 5회 실패 시 계정이 600초간 잠기도록 제어되며, PAM 인증 사슬 붕괴를 막기 위해 텍스트 강제 주입 대신 `/usr/share/pam-configs/custom-faillock` 커스텀 프로필이 생성되어 시스템에 적용됩니다.
* `/etc/shadow` 권한이 우분투 내부 인증 도우미(`unix_chkpwd`) 호환성을 위해 `0640` 및 `shadow` 그룹으로 조율되어, 로컬 인증 기능은 보존하면서 외부로의 해시 유출을 방어합니다.
* `hosts.deny`에 `ALL: ALL`이 주입되어 화이트리스트 IP 외의 SSH 접근이 원천 차단됩니다.
* 취약 패키지들이 설정 파일까지 완전히 제거(`purge`)되며, `nfs-server` 등은 수동 구동도 차단되도록 마스킹(`masked`) 처리됩니다.
* 시간 동기화 오탐 유발 데몬(ntp, chrony)이 완전 삭제되며, 클라우드 최소 이미지 환경을 고려하여 systemd-timesyncd 패키지의 명시적 설치 및 커널 단위의 자동 동기화(set-ntp true)가 강제 적용됩니다.
* `/etc/crontab` 권한이 `0640`으로 조율되고, 새로 생성된 `/etc/cron.allow` 화이트리스트에 의해 명시된 사용자(root)만 예약 작업을 수행할 수 있도록 제한됩니다.
* 물리 디스크(ext4, xfs)만을 정밀 타겟팅하여 가상 파일 시스템 오탐 없이 World-writable 취약점을 제거합니다.

## 변수 설명

### 1. 계정 및 인증 정책 변수 (`account.yml` 연계)

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `sshd_permit_root_login` | `no` | SSH 서비스를 통한 root 계정의 직접 원격 로그인 허용 여부입니다. |
| `os_pass_max_days` | `90` | `/etc/login.defs`에 반영될 패스워드 최대 사용 유효 기간(일)입니다. |
| `pam_pwquality_retry` | `3` | 패스워드 변경 시 입력 레이아웃 최대 재시도 횟수입니다. |
| `pam_pwquality_minlen` | `8` | 생성 가능한 패스워드의 최소 길이 요구사항입니다. |
| `pam_pwquality_lcredit` | `-1` | 패스워드 내 영문 소문자 필수 포함 최소 개수 조건입니다. (-1은 최소 1개 이상 필수) |
| `pam_pwquality_ucredit` | `-1` | 패스워드 내 영문 대문자 필수 포함 최소 개수 조건입니다. |
| `pam_pwquality_dcredit` | `-1` | 패스워드 내 숫자 필수 포함 최소 개수 조건입니다. |
| `pam_pwquality_ocredit` | `-1` | 패스워드 내 특수문자 필수 포함 최소 개수 조건입니다. |
| `pam_deny_count` | `5` | 계정 잠금을 유발하는 임계치 로그인 실패 연속 허용 횟수입니다. |
| `pam_unlock_time` | `600` | 로그인 실패로 계정 잠금 처리가 되었을 때의 유지 시간(초)입니다. |

### 2. 파일 및 접근 제어 정책 변수 (`file.yml` 연계)

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `file_owner_root` | `root` | 시스템 주요 보안 설정 파일들의 안전한 마스터 소유자 계정명입니다. |
| `file_group_root` | `root` | 시스템 주요 보안 설정 파일들의 안전한 마스터 소유 그룹명입니다. |
| `file_group_shadow` | `shadow` | Ubuntu 고유의 패스워드 인증 도우미(`unix_chkpwd`) 접근을 보장하기 위한 shadow 파일 전용 그룹명입니다. |
| `file_mode_755` | `0755` | 일반 실행 파일 및 권한 분리 공유 디렉터리에 적용할 권한입니다. |
| `file_mode_700` | `0700` | root 홈 디렉터리 등 외부 접근이 차단되어야 하는 관리자 전용 디렉터리 권한입니다. |
| `file_mode_644` | `0644` | 일반 설정 파일 및 공공 조회 텍스트 파일의 수정 권한 제한용 기본 권한입니다. |
| `file_mode_640` | `0640` | 스케줄러 디렉터리 및 패스워드 해시 파일(Ubuntu) 등 특정 그룹만 읽기가 가능해야 하는 파일 권한입니다. |
| `file_mode_400` | `0400` | 기타 초민감 정보 관리를 위한 관리자 전용 읽기 권한입니다. |
| `allowed_ssh_ips` | `[]` | hosts.allow에 등록되어 방화벽을 통과할 안전한 관리자 네트워크 IP/대역 리스트입니다. (빈 값 가능) |
| `unnecessary_suid_sgid_files` | (취약 바이너리 목록) | 권한 상승 취약점 악용을 막기 위해 SUID/SGID 비트를 제거할 실행 파일 경로 목록입니다. |
| `os_scan_fstypes` | `-fstype ext4 -o -fstype xfs` | 가상 파일 시스템(/sys, /proc 등) 오탐 방지를 위해 World-writable 점검 시 스캔을 허용할 물리 디스크 타입들입니다. |
| `os_scan_exclude_paths` | `-path /tmp -prune -o -path /var/tmp -prune` | World-writable 점검 시 정상적인 OS 런타임 보장을 위해 내부 스캔을 건너뛸(prune) 임시 디렉터리 조건입니다. |

### 3. 서비스 통제 정책 변수 (`service.yml` 및 `account.yml` 연계)

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `package_ssh_server` | `openssh-server` | 보안 기반 형성을 위해 사전 체크 및 설치할 SSH 서버 패키지명입니다. |
| `package_netbase` | `netbase` | 네트워크 서비스 포트 무결성을 위해 사전 구성할 기본 베이스 패키지명입니다. |
| `package_pam_pwquality` | `libpam-pwquality` | 패스워드 복잡도 정책 적용을 위해 사전 설치할 필수 PAM 모듈 패키지명입니다. |
| `unnecessary_packages` | `[finger, tftpd, talk, ...]` | 시스템 보안 표면 최소화를 위해 아예 박멸(`purge`) 처리할 레거시 패키지 목록입니다. |
| `xinetd_vulnerable_services` | `[echo, discard, ...]` | xinetd 수퍼 데몬 하위에서 비활성화(`disable = yes`) 조치할 취약 서비스 목록입니다. |
| `standalone_services_to_disable` | `[nfs-server, rpcbind, ...]` | 원격 취약점 노출 차단을 위해 데몬을 즉시 중지하고 마스킹(`masked: yes`) 처리할 독립 서비스 목록입니다. |

### 4. 시스템 환경 및 경로 변수 (`system.yml`, `service.yml`, `account.yml` 연계)

| 변수 | 기본값 | 설명 |
| --- | --- | --- |
| `system_timezone` | `Asia/Seoul` | 중앙 로그 보존 및 타임라인 정렬을 위해 강제 설정할 인프라 기준 시간대입니다. |
| `apply_security_updates` | `yes` | 인프라 배포 시점에 알려진 취약점을 자동 방어하기 위한 최신 패키지 디스트 업데이트 여부입니다. |
| `legacy_ntp_packages` | `[ntp, chrony]` | 중복 동기화 오탐 방지를 위해 확실히 제거할 구형 타임 데몬 리스트입니다. |
| `package_timesyncd` | `systemd-timesyncd` | 가상화 인프라 무결성을 위해 명시적으로 설치를 보장할 표준 타임 데몬 패키지명입니다. |
| `service_timesyncd` | `systemd-timesyncd` | 가상화 인프라 무결성을 위해 구동 및 보장할 최종 타임 데몬 서비스명입니다. |
| `cron_directories` | `[/etc/cron.hourly, ...]` | 악의적인 백도어 유지를 방어하기 위해 타 사용자 쓰기 권한(o-w)을 일괄 거부할 cron 경로 폴더 리스트입니다. |
| `path_check_target_files` | `[/etc/profile, ...]` | PATH 변수 내 `.` 관리를 위해 순회 스캔할 핵심 셸 환경 파일 리스트입니다. |
| `path_xinetd_dir` | `/etc/xinetd.d` | xinetd 기반 레거시 설정들의 탐색 베이스 디렉터리 경로입니다. |
| `path_vsftpd_conf` | `/etc/vsftpd.conf` | Anonymous FTP 점검 및 차단 정책을 적용할 vsftpd 메인 설정 파일 경로입니다. |
| `path_proftpd_conf` | `/etc/proftpd/proftpd.conf` | 익명 인증 우회를 차단하기 위해 수정할 proftpd 메인 설정 파일 경로입니다. |
| `path_pam_faillock_conf` | `/usr/share/pam-configs/custom-faillock` | 인증 사슬 붕괴를 방지하고 안전하게 faillock 정책을 주입할 Ubuntu 표준 PAM 커스텀 프로필 경로입니다. |
| `path_sshd_config` 외 | `/etc/ssh/sshd_config` 등 | 각 태스크 파일 내에서 멱등성 주입 대상을 정밀 지정하기 위한 시스템 핵심 설정 파일들의 경로 매핑 변수군입니다. |