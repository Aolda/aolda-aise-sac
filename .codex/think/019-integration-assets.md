# Commit 019: Integration assets

## Faced Problem

KVM, Ceph, and Storage roles were implemented as separate responsibility boundaries. Operators still need a clear way to run them together or by tag without changing the repository's top-level architecture.

## Reasoning

I added a single integration playbook under the existing `playbooks` directory and kept inventory groups aligned with the approved names: `kvm_hosts`, `ceph_hosts`, and `storage_hosts`. I added group variable files for Ceph and Storage that preserve report-oriented defaults.

## Decision

The integrated playbook is `playbooks/security_baseline.yml`. It runs each role against its own host group. The inventory file remains an example with commented hosts.

## Why

This preserves the existing architecture while making the full project scope executable. It also keeps real environment values out of the repository until operators provide them.
