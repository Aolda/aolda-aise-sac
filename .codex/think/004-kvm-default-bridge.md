# Commit 004: KVM default bridge

## Faced Problem

The libvirt `default` network can be unnecessary in OpenStack Neutron-based KVM environments, but destroying or undefining it can affect workloads if the environment still depends on `virbr0`.

## Reasoning

I implemented the control as a staged state machine. The role first reports `virsh net-info`. Enforcement can then disable autostart, destroy an active network, or undefine it, but each stronger action requires both an action value and a boolean guard.

## Decision

The default is `enable_kvm_default_bridge_disable: false` and `kvm_default_bridge_action: report`. Actual changes require `security_action_mode: enforce`.

## Why

This follows the principle that destructive or connectivity-affecting operations should be opt-in. It also gives operators a clear operational sequence that mirrors libvirt's own lifecycle.
