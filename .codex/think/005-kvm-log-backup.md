# Commit 005: KVM log backup

## Faced Problem

KVM and libvirt logs are important evidence, but log rotation and backup paths differ by environment. A hardcoded rotation file would make later policy changes difficult.

## Reasoning

I parameterized log paths, rotation period, retention count, compression, and backup destination. The logrotate file is validated with `logrotate -d` before installation. Backup execution is optional because copying logs can consume storage and should be enabled intentionally.

## Decision

The molecule reports configured policy by default. Enforce mode deploys the logrotate configuration. Backup execution additionally requires `kvm_log_backup_enabled: true`.

## Why

This makes log evidence management repeatable without forcing every host to perform storage-consuming backups on the first run.
