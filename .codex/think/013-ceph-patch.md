# Commit 013: Ceph patch

## Faced Problem

Ceph patching is cluster-sensitive. Applying packages without checking health can amplify an existing outage, and rebooting storage nodes without a rolling plan can reduce availability.

## Reasoning

I added health reporting and an enforce-time health assertion before package changes. The role supports package update modes but keeps reboot behind a separate flag. It does not orchestrate a full cluster rolling upgrade because inventory-specific batching and service drain rules need operator policy.

## Decision

Defaults keep patching disabled and in report mode. Enforcement requires `enable_ceph_patch: true`, `security_action_mode: enforce`, and a non-report patch mode.

## Why

This provides patch visibility and a controlled local patch primitive while avoiding unsafe cluster orchestration assumptions.
