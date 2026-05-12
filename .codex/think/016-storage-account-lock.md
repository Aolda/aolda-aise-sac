# Commit 016: Storage account lock

## Faced Problem

Login failure lockout protects against brute force attacks, but overly aggressive lockout can block administrators, especially if root or sudo users are included.

## Reasoning

I used `faillock.conf` as the policy surface for Ubuntu 24.04. Root lockout and admin group exemption remain separate policy variables because they carry different operational risks.

## Decision

The molecule reports the intended thresholds by default. Enforce mode writes the managed faillock configuration.

## Why

This provides a clear account lockout baseline without silently changing administrator lockout behavior.
