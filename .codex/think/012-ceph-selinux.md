# Commit 012: Ceph SELinux

## Faced Problem

The policy guide includes Ceph SELinux, but Ubuntu 24.04 commonly uses AppArmor rather than SELinux as the primary mandatory access control system. Enforcing SELinux blindly could break Ceph services.

## Reasoning

I implemented SELinux as a cautious Ubuntu-compatible control. It can report status and recent AVC audit events even if SELinux tools are absent. Package installation and `setenforce` are possible only when explicitly enabled.

## Decision

Defaults keep `enable_ceph_selinux: false` and package installation disabled. Reboot is separately guarded by `ceph_selinux_allow_reboot`.

## Why

This satisfies the policy surface while respecting Ubuntu's default security model and the operational risk of Ceph SELinux enforcement.
