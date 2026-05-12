# Storage Security Baseline Role

Ubuntu 24.04 storage host OS security baseline role. The role is safe by default and applies changes only when `security_action_mode: enforce` or a stronger explicit mode is selected.

## Molecules

- `storage_root_ssh`
- `storage_password_complexity`
- `storage_account_lock`
- `storage_password_age`
- `storage_accounts`
