# Commit 022: Inventory empty groups

## Faced Problem

The YAML inventory used `hosts:` keys with only commented examples underneath. YAML parses those as null values, which is less safe for Ansible inventory handling.

## Reasoning

Empty groups should be represented as empty dictionaries. Examples can remain as comments beside the valid structure.

## Decision

I changed each example group to `hosts: {}` and moved sample host definitions into a commented example block.

## Why

This keeps the example inventory valid and unambiguous even before real hosts are added.
