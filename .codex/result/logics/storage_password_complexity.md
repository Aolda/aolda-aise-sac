# storage_password_complexity

## 기능 한줄정리

Ubuntu Storage 호스트의 패스워드 복잡도 기준을 `libpam-pwquality` 설정으로 관리합니다.

## 적용방법

1. 기본 report로 패스워드 복잡도 목표값을 확인합니다.
2. 실제 적용은 `security_action_mode: enforce`에서 수행합니다.
3. enforce 모드에서 `libpam-pwquality`를 설치하고 drop-in 설정을 배포합니다.

## 제공인자

| 인자 | 기본값 | 설명 |
|---|---:|---|
| `enable_storage_password_complexity` | `true` | 기능 활성화 여부 |
| `password_minlen` | `12` | 최소 길이 |
| `password_dcredit` | `-1` | 숫자 요구 기준 |
| `password_ucredit` | `-1` | 대문자 요구 기준 |
| `password_lcredit` | `-1` | 소문자 요구 기준 |
| `password_ocredit` | `-1` | 특수문자 요구 기준 |
| `password_retry` | `3` | 재시도 횟수 |
| `password_dictcheck` | `true` | 사전 단어 검사 여부 |
| `storage_pwquality_config_path` | `/etc/security/pwquality.conf.d/99-storage-security.conf` | pwquality 설정 경로 |

## 세부 진행단계

1. 복잡도 정책값을 report로 출력합니다.
2. enforce 모드에서 `libpam-pwquality` 패키지를 설치합니다.
3. pwquality drop-in 디렉터리를 생성합니다.
4. `pwquality-storage.conf.j2` 템플릿을 렌더링합니다.
5. 최소 길이, 문자 종류 요구값, retry, dictcheck 값을 설정 파일에 반영합니다.

## 단일기능 실행방법

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags storage_password_complexity \
  --limit storage_hosts \
  --check --diff
```

```bash
ansible-playbook -i inventory/hosts.yml playbooks/security_baseline.yml \
  --tags storage_password_complexity \
  --limit storage_hosts \
  -e "security_action_mode=enforce"
```
