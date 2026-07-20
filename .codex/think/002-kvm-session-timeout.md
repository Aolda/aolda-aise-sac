# Commit 002: KVM session timeout

## Faced Problem

The implementation rules require SSH and shell timeout controls with configurable policy values. On Ubuntu 24.04, an incorrect SSH configuration can immediately disrupt administration access.

## Reasoning

I used an SSH drop-in file instead of editing `/etc/ssh/sshd_config` directly. This keeps the change isolated and easier to roll back. The task validates the generated file with `sshd -t` before notifying a reload handler. Shell timeout is written through `/etc/profile.d`, which is the standard place for login shell environment policy.

## Decision

The molecule runs in report mode by default. Files are written only when `security_action_mode == 'enforce'`. The required tag is `kvm_session_timeout`.

## Why

This gives operators a safe preview path while still providing an idempotent enforcement path. It also avoids modifying base distribution files directly, which is safer for Ubuntu LTS maintenance.
