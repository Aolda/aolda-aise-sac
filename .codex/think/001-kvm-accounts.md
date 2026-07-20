# Commit 001: KVM account hardening

## Faced Problem

The existing KVM role locked accounts automatically when they were inactive for 60 days. That behavior did not match the implementation rule that dangerous work must run only in an explicit action mode. The role also kept important policy values under a nested group variable and did not provide role defaults.

## Reasoning

I kept the current `roles/kvm-account-audit` role because it is the existing architecture for KVM account control. Replacing it with a new top-level role would create unnecessary migration risk. I added `defaults/main.yml` so every policy value has a safe baseline and remains overrideable from `group_vars` or `host_vars`.

The default action is now `security_action_mode: report` and `kvm_account_action: report`. This means a normal run creates evidence and recommendations, but does not lock or delete accounts. Locking requires both `security_action_mode: enforce` and `kvm_account_action: lock`. Deletion requires both `security_action_mode: delete` and `kvm_account_action: delete`.

## Decision

I split the KVM account logic into `tasks/accounts.yml` and made `tasks/main.yml` import it with the required `kvm_accounts` tag. I preserved compatibility with the previous `kvm_account_audit` nested variable so existing group vars continue to work while the role gains proper defaults.

## Why

This keeps the current role usable, reduces operational risk, and matches the SaC rule that policy values must not be hardcoded inside tasks. It also makes the first molecule independently runnable and commit-ready.
