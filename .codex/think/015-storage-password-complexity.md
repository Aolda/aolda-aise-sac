# Commit 015: Storage password complexity

## Faced Problem

Password complexity protects local accounts, but PAM-related changes can affect login and password change behavior. The settings also need to remain adjustable as policy changes.

## Reasoning

Ubuntu 24.04 uses `libpam-pwquality` for common password quality controls. I added a dedicated drop-in under `/etc/security/pwquality.conf.d` instead of modifying the main config file.

## Decision

The molecule reports configured values by default. Enforce mode installs `libpam-pwquality` and writes the managed policy file.

## Why

This makes password policy explicit, reversible, and aligned with Ubuntu's package-supported mechanism.
