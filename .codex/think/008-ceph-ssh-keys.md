# Commit 008: Ceph SSH keys

## Faced Problem

Ceph administrative SSH keys are often used for node operations. Weak file modes expose private keys, but automatically purging authorized keys can remove valid operational access.

## Reasoning

I split permission hardening from key content management. Directory and private-key modes can be enforced safely in controlled mode. Authorized key content is managed only when an explicit per-user policy exists and `ceph_manage_authorized_keys` is true.

## Decision

The molecule reports discovered user homes and policy state. Enforcement fixes `.ssh` directory and private key permissions. Authorized key replacement remains opt-in.

## Why

This improves key hygiene without surprising operators by deleting or replacing login keys.
