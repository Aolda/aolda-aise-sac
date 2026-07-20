# Commit 014: Storage root SSH

## Faced Problem

Restricting root SSH is a strong security control, but applying it without a verified replacement admin account can lock operators out of storage hosts.

## Reasoning

I implemented the setting as an SSH drop-in rather than editing the base sshd config. This keeps the managed change isolated. Enforcement is gated by `security_action_mode: enforce`.

## Decision

Defaults express a secure target state, but the role reports by default. The drop-in is written only in enforce mode and validated with `sshd -t`.

## Why

This provides a clear and reversible root SSH policy while respecting the operational risk of remote access changes.
