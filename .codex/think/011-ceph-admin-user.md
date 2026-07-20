# Commit 011: Ceph admin user

## Faced Problem

Using root directly for Ceph operations weakens auditability, but changing administrator access can lock out operators if replacement accounts are not prepared.

## Reasoning

I implemented admin user creation, group membership, and sudoers as an enforce-only control. Root SSH restriction is controlled by a separate boolean and remains disabled by default.

## Decision

The molecule reports intended users and groups by default. It creates users and sudoers only in `security_action_mode: enforce`. Sudoers is validated with `visudo`.

## Why

This supports a migration away from root operations while preserving a safe default for existing environments.
