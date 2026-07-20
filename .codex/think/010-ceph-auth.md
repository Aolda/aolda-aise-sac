# Commit 010: Ceph auth

## Faced Problem

CephX is a core Ceph authentication mechanism. Enabling or changing it can affect Glance, Cinder, Nova, and native Ceph clients if their keyrings are not prepared.

## Reasoning

I treated CephX as a high-risk control. The role can query current auth settings, but changes require both the CephX enable flag and report-only flag to be intentionally changed. Client keyring deployment is also separate because secret material must come from approved inventory or vault data.

## Decision

Defaults remain `enable_cephx_enforcement: false` and `ceph_auth_report_only: true`. Enforcement uses `ceph config set mon` only when explicitly allowed.

## Why

This prevents accidental cluster authentication changes while still giving the SaC project a controlled path to enforce CephX later.
