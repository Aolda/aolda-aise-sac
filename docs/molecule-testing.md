# Molecule 테스트 가이드

개인별 가상 인스턴스에서 담당 role을 검증하기 위한 Molecule 실행 절차입니다.

이 저장소의 Molecule 시나리오는 `delegated` 방식입니다. Molecule이 VM을 직접 생성하지 않고, 사용자가 만든 개인 VM에 SSH로 접속해 role을 실행합니다. 클라우드 계정, 과금, 이미지 차이를 저장소에 묶지 않기 위한 방식입니다.

## 1. 개인 VM 준비

각자 담당 파트에 맞는 VM을 생성합니다.

| 담당 | VM에 준비할 것 |
| --- | --- |
| DB | MariaDB 또는 MySQL 설치 |
| Docker | Docker Engine 설치 |
| Kubernetes | kubeadm 기반 control plane 또는 worker |
| OpenStack | 테스트할 컴포넌트 설정파일이 존재하는 OpenStack 노드 |

SSH 접속이 가능해야 합니다.

```bash
ssh <user>@<vm-ip>
```

## 2. 로컬 의존성 설치

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
ansible-galaxy collection install -r requirements.yml
```

## 3. 공통 환경변수

Molecule 실행 전에 대상 VM 정보를 지정합니다.

```bash
export MOLECULE_TARGET_HOST=<VM_IP>
export MOLECULE_TARGET_USER=<SSH_USER>
export MOLECULE_TARGET_PRIVATE_KEY_FILE=<SSH_PRIVATE_KEY_PATH>
```

비밀번호 접속을 사용한다면 `MOLECULE_TARGET_PRIVATE_KEY_FILE` 대신 Ansible SSH 옵션을 별도로 사용합니다.

## 3-1. 프로젝트 전체 문법/스모크 테스트

전체 role과 playbook이 Ansible 문법 수준에서 깨지지 않았는지 Molecule로 확인합니다.

```bash
molecule test -s project-syntax
```

이 시나리오는 실제 DB/Docker/Kubernetes/OpenStack 서비스를 변경하지 않습니다. 각 role 테스트 playbook, OpenStack playbook, Molecule converge/verify playbook의 syntax check를 한 번에 수행합니다.

## 4. DB 테스트

```bash
molecule test -s db-security
```

운영 영향이 있는 항목은 기본 비활성으로 둡니다.

```bash
export DB_APPLY_SECURITY_PATCH=false
export DB_SET_DEFAULT_AUTH_PLUGIN=false
```

## 5. Docker 테스트

```bash
molecule test -s docker-security
```

로컬 Docker 컨테이너만 사용해서 빠르게 검증하려면 아래 시나리오를 사용합니다.

```bash
molecule test -s docker-security-docker
```

이 Docker 기반 시나리오는 컨테이너 환경 한계 때문에 auditd, 실제 Docker daemon 설정, 런타임 컨테이너 점검은 꺼두고 파일 권한과 Content Trust 설정을 검증합니다.

패키지 업데이트와 daemon 보안 설정은 기본 비활성입니다.

```bash
export DOCKER_APPLY_PACKAGE_UPDATE=false
export DOCKER_APPLY_DAEMON_SECURITY=false
export DOCKER_FAIL_ON_RUNTIME_POLICY_VIOLATION=false
```

강제 실패 검증까지 하고 싶을 때만 `DOCKER_FAIL_ON_RUNTIME_POLICY_VIOLATION=true`로 바꿉니다.

## 6. Kubernetes 테스트

```bash
molecule test -s k8s-security
```

앱 통신을 끊을 수 있는 정책은 기본 비활성입니다.

```bash
export K8S_ENABLE_NETWORK_POLICIES=false
export K8S_DISABLE_DEFAULT_SA_TOKEN_AUTOMOUNT=false
export K8S_FAIL_ON_POLICY_VIOLATION=false
```

## 7. OpenStack 컴포넌트 테스트

OpenStack은 컴포넌트별로 하나씩 테스트합니다.

```bash
export MOLECULE_OPENSTACK_COMPONENT=keystone
molecule test -s openstack-component
```

가능한 값:

- `keystone`
- `nova`
- `cinder`
- `glance`
- `neutron`
- `horizon`

TLS, Horizon Secure Cookie, Cinder 볼륨 암호화는 실제 HTTPS endpoint, 인증서, Barbican/KMS가 준비된 경우에만 별도 변수로 활성화합니다.

## 8. 블로그 작성 내용

아래 항목을 캡처 또는 로그와 함께 정리합니다.

- 테스트 목적
- 테스트 VM 정보: OS, IP, CPU/RAM, 설치 컴포넌트 버전
- 실행 명령
- 적용 전 상태
- Molecule 실행 결과
- 적용 후 변경 사항
- 실패/경고가 있었다면 원인과 조치
- 위험해서 기본 비활성으로 둔 항목
- 느낀 점 또는 개선할 점
