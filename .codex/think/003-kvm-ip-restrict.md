# Commit 003: KVM IP restriction

## Faced Problem

IP restriction protects management ports, but it can also lock operators out or break OpenStack, Ceph, and Kolla communication. The implementation guide therefore marks this control as disabled by default.

## Reasoning

Ubuntu 24.04 commonly uses `ufw` as a simple host firewall interface. I limited enforcement to `ufw` so the role does not pretend to safely support firewalld, nftables, and iptables without separate validation. Other backends can still be represented in variables, but enforce mode stops with a clear assertion.

## Decision

The molecule stays inactive unless `enable_kvm_ip_restrict` is true. Even then, actual changes require `security_action_mode: enforce` and `firewall_apply_mode: enforce`. Default deny is separated behind `enable_default_deny` because it is the riskiest part.

## Why

This keeps the implementation useful for Ubuntu LTS while avoiding an overly broad firewall abstraction. It also gives operators a staged path: define CIDRs, run report/check mode, then enforce on test hosts.
