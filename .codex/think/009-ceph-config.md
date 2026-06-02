# Commit 009: Ceph config

## Faced Problem

`ceph.conf` can be a normal configuration file, but in some environments it may contain secrets or key-like values. A single hardcoded mode is not always appropriate.

## Reasoning

I added a lightweight scan for configured sensitive patterns. Files that match use the stricter secret mode, while normal files use the default config mode.

## Decision

The molecule reports file state and scan classification by default. Enforcement applies owner, group, and mode only in `security_action_mode: enforce`.

## Why

This respects operational differences while preserving a clear policy mechanism for stricter handling of sensitive configuration files.
