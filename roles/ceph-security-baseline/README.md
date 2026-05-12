# Ceph Security Baseline Role

Ubuntu 24.04 Ceph hosts security baseline role. The role is intentionally safe by default: sensitive controls run in report mode unless both the enable flag and enforcement variables are set.

## Molecules

- `ceph_keyring`
- `ceph_ssh_keys`
- `ceph_config`
- `ceph_auth`
- `ceph_admin_user`
- `ceph_selinux`
- `ceph_patch`
