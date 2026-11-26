#!/usr/bin/env python3
"""Small, explicit defect-seeding benchmark. This is not exhaustive mutation coverage."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

MUTANTS = [
    (1, "numeric-days", "roles/kvm-account-audit/module_utils/kvm_policy.py", "int(days) >= restriction_days", "str(days) >= str(restriction_days)", "test_policy.AccountPolicyTests"),
    (1, "protected-account", "roles/kvm-account-audit/module_utils/kvm_policy.py", "if name in protected:", "if False and name in protected:", "test_policy.AccountPolicyTests"),
    (1, "implicit-key-replacement", "roles/ceph-security-baseline/filter_plugins/ceph_keys.py", "if replace and not confirmed:", "if False and replace and not confirmed:", "test_policy.AuthorizedKeyTests"),
    (1, "remove-management-key", "roles/ceph-security-baseline/filter_plugins/ceph_keys.py", "if any(key not in lines for key in required):", "if False and any(key not in lines for key in required):", "test_policy.AuthorizedKeyTests"),
    (2, "duplicate-snapshot", "roles/kvm-account-audit/library/kvm_log_snapshot.py", "return False", "return True", "test_idempotency.SnapshotTests"),
    (2, "snapshot-check-writes", "roles/kvm-account-audit/library/kvm_log_snapshot.py", "if check:", "if False and check:", "test_idempotency.SnapshotTests"),
    (2, "repeat-ceph-auth-set", "roles/ceph-security-baseline/tasks/auth.yml", "item.stdout | trim != ceph_auth_targets[item.item]", "true", "test_idempotency.CephCommandIntegration"),
    (3, "ssh-check-writes", "plugins/modules/security_sshd_dropin.py", "if check: return changed", "if False and check: return changed", "test_operations.SshTransactionTests"),
    (3, "ignore-effective-ssh", "plugins/modules/security_sshd_dropin.py", "if any(actual.get(key.lower()) != str(value) for key, value in expected.items()):", "if False and any(actual.get(key.lower()) != str(value) for key, value in expected.items()):", "test_operations.SshTransactionTests"),
    (3, "parallel-maintenance", "playbooks/security_baseline.yml", "serial: 1", "serial: 2", "test_operations.OperationContracts"),
    (4, "unknown-is-compliant", "plugins/filter/security_evidence.py", 'elif not available: status = "unknown"', 'elif not available: status = "compliant"', "test_reporting.EvidenceTests"),
    (4, "unverified-apply-success", "plugins/filter/security_evidence.py", 'elif observed != expected: status = "needs_action"', 'elif observed != expected: status = "applied"', "test_reporting.EvidenceTests"),
]

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo", type=Path, default=Path(__file__).resolve().parents[2])
    parser.add_argument("--stage", type=int, choices=[1,2,3,4])
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    records = []
    for stage, name, relative, old, new, suite in MUTANTS:
        if args.stage and stage != args.stage: continue
        with tempfile.TemporaryDirectory(prefix="aise-mutation-") as directory:
            root = Path(directory) / "repo"
            shutil.copytree(args.repo, root, ignore=shutil.ignore_patterns(".git", ".venv", "__pycache__", "reports", ".ansible"))
            path = root / relative
            if old not in path.read_text():
                records.append(dict(stage=stage, defect=name, status="invalid"))
                continue
            path.write_text(path.read_text().replace(old,new,1))
            result = subprocess.run([sys.executable, "-m", "unittest", suite], cwd=root / "tests/kvm_ceph", capture_output=True, text=True)
            # A test assertion must fail; import/syntax/setup errors are not credited as detections.
            killed = result.returncode != 0 and "FAIL:" in result.stderr and "ERROR:" not in result.stderr
            records.append(dict(stage=stage, defect=name, status="detected" if killed else "survived_or_invalid"))
    output = dict(registered=len(records), detected=sum(r["status"]=="detected" for r in records), cases=records)
    print(json.dumps(output, ensure_ascii=False, indent=2))
    if args.output: args.output.write_text(json.dumps(output,ensure_ascii=False,indent=2)+"\n")
    return 0 if output["detected"]==output["registered"] else 1

if __name__ == "__main__": sys.exit(main())
