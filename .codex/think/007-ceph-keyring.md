# Commit 007: Ceph keyring

## Faced Problem

Ceph keyrings contain authentication secrets. Incorrect permissions can expose cluster access, but changing keyring ownership or mode without knowing service requirements can interrupt Ceph or OpenStack clients.

## Reasoning

I created a dedicated `ceph-security-baseline` role because Ceph controls have a different risk profile from KVM and Storage OS controls. The keyring molecule uses explicit policy entries so operators decide which files Ansible is allowed to manage.

## Decision

The default is report-only. Enforcement requires `security_action_mode: enforce` and `ceph_keyring_report_only: false`.

## Why

This gives immediate visibility into keyring state while preventing accidental permission changes on production clusters.
