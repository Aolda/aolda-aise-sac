# Commit 018: Storage accounts

## Faced Problem

Unused accounts are risky, but deleting or locking the wrong storage host account can interrupt automation or service operations.

## Reasoning

I used explicit retired, allowed, and excluded lists instead of deriving deletion candidates automatically. This makes the operator's intent visible in policy variables.

## Decision

Report mode lists effective targets. Locking requires `security_action_mode: enforce` and `storage_account_action: lock`. Deletion requires `security_action_mode: delete` and `storage_account_action: delete`.

## Why

This provides account cleanup automation while keeping destructive actions opt-in and auditable.
