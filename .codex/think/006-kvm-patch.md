# Commit 006: KVM patch

## Faced Problem

KVM, QEMU, and libvirt security updates are necessary, but applying them on compute hosts can affect running virtual machines and OpenStack Nova scheduling.

## Reasoning

I made report mode show `apt-cache policy` output for the configured packages. Enforcement uses Ubuntu's `apt` module and keeps reboot separate behind `kvm_allow_reboot`. I did not automate Nova compute drain because the repository does not yet contain OpenStack credentials or an approved drain workflow.

## Decision

The molecule supports `report`, `security_only`, `latest`, and `specific_version` modes. Actual package changes require `enable_kvm_patch: true` and `security_action_mode: enforce`.

## Why

This gives operators patch visibility immediately while keeping disruptive patch and reboot actions explicit. It also leaves room to add an environment-specific drain workflow later.
