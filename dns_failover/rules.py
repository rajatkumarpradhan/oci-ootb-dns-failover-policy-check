"""DNS001-DNS004 rules for FAILOVER steering policies."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from .model import MAX_TTL_SECONDS, Snapshot


@dataclass(frozen=True)
class Finding:
    rule: str
    severity: str  # HIGH | MEDIUM | LOW
    policy: str
    detail: str


def rule_empty_pool(snapshot: Snapshot) -> list:
    """DNS001 HIGH: a referenced pool has zero enabled answers."""
    out = []
    for p in snapshot.policies:
        pools = defaultdict(int)
        for a in p.answers:
            if a.enabled:
                pools[a.pool] += 1
        referenced = {a.pool for a in p.answers}
        for pool in sorted(referenced):
            if pools.get(pool, 0) == 0:
                out.append(
                    Finding(
                        rule="DNS001",
                        severity="HIGH",
                        policy=p.display_name,
                        detail=(
                            f"pool {pool!r} has no enabled answers; if failover sends traffic "
                            f"there, nothing answers"
                        ),
                    )
                )
    return out


def rule_priority_gaps(snapshot: Snapshot) -> list:
    """DNS002 MEDIUM: priorities are not exactly 1..N (gaps or duplicates)."""
    out = []
    for p in snapshot.policies:
        prios = sorted(a.priority for a in p.answers if a.enabled)
        if not prios:
            continue  # empty everywhere is DNS001's job
        expected = list(range(1, len(prios) + 1))
        if prios != expected:
            out.append(
                Finding(
                    rule="DNS002",
                    severity="MEDIUM",
                    policy=p.display_name,
                    detail=f"enabled answer priorities are {prios}, expected {expected}; failover order is ambiguous",
                )
            )
    return out


def rule_no_health_check(snapshot: Snapshot) -> list:
    """DNS003 MEDIUM: policy has no health check attached."""
    out = []
    for p in snapshot.policies:
        if not p.health_check_id:
            out.append(
                Finding(
                    rule="DNS003",
                    severity="MEDIUM",
                    policy=p.display_name,
                    detail="no health check attached; failover cannot see endpoint health",
                )
            )
    return out


def rule_long_ttl(snapshot: Snapshot) -> list:
    """DNS004 LOW: TTL above MAX_TTL_SECONDS slows failover."""
    out = []
    for p in snapshot.policies:
        if p.ttl > MAX_TTL_SECONDS:
            out.append(
                Finding(
                    rule="DNS004",
                    severity="LOW",
                    policy=p.display_name,
                    detail=f"TTL is {p.ttl}s (> {MAX_TTL_SECONDS}); resolvers keep the dying endpoint too long",
                )
            )
    return out


ALL_RULES = (
    rule_empty_pool,
    rule_priority_gaps,
    rule_no_health_check,
    rule_long_ttl,
)

_SEVERITY_RANK = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


def run_all(snapshot: Snapshot) -> list:
    findings = []
    for rule in ALL_RULES:
        findings.extend(rule(snapshot))
    findings.sort(key=lambda f: (_SEVERITY_RANK[f.severity], f.rule, f.policy))
    return findings


def exit_code(findings: list) -> int:
    if any(f.severity == "HIGH" for f in findings):
        return 2
    if findings:
        return 1
    return 0
