# Commit 017: Storage password age

## Faced Problem

Password aging is useful for human accounts but can break service and automation accounts if applied broadly.

## Reasoning

I used explicit target and excluded user lists. This makes the policy intentionally scoped and avoids discovering every local account and changing it automatically.

## Decision

The molecule is disabled by default. Even when enabled, applying to existing users requires `password_age_apply_existing_users: true` and `security_action_mode: enforce`.

## Why

This protects service accounts and gives operators a controlled rollout path for password aging.
