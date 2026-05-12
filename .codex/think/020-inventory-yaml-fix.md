# Commit 020: Inventory YAML fix

## Faced Problem

The inventory file was named `hosts.yml` but used INI-style group syntax. The repository already had this mismatch, and the integration update extended it with new groups.

## Reasoning

Because the file extension is YAML and the new integration playbook relies on clear group names, converting the example inventory to YAML is less ambiguous than keeping INI content in a `.yml` file.

## Decision

I converted `inventory/hosts.yml` to a YAML inventory with commented example hosts under `kvm_hosts`, `ceph_hosts`, and `storage_hosts`.

## Why

This aligns file content with file naming, makes static YAML validation possible, and reduces confusion for operators editing host examples.
