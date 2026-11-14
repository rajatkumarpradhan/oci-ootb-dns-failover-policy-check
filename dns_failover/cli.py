"""python -m dns_failover.cli SNAPSHOT"""

from __future__ import annotations

import argparse
import sys

from .model import SnapshotError, load_snapshot
from .rules import exit_code, run_all


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="dns-failover-check",
        description="Check an offline snapshot of OCI DNS FAILOVER steering policies.",
    )
    p.add_argument("snapshot", help="path to the JSON policy snapshot")
    return p


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        snapshot = load_snapshot(args.snapshot)
    except SnapshotError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    findings = run_all(snapshot)
    print(f"DNS failover check - {len(snapshot.policies)} policy/policies, {len(findings)} finding(s)")
    for f in findings:
        print(f"[{f.severity:6s}] {f.rule} policy={f.policy}")
        print(f"         {f.detail}")
    code = exit_code(findings)
    print({0: "RESULT: clean", 1: "RESULT: warnings only", 2: "RESULT: HIGH findings present"}[code])
    return code


if __name__ == "__main__":
    raise SystemExit(main())
