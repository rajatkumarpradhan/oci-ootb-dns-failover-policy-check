"""Data model + snapshot loading for steering-policy checks."""

from __future__ import annotations

import json
from dataclasses import dataclass


class SnapshotError(ValueError):
    """Raised when a snapshot file is malformed."""


MAX_TTL_SECONDS = 300


@dataclass(frozen=True)
class Answer:
    name: str
    pool: str
    priority: int
    enabled: bool
    rdata: str


@dataclass(frozen=True)
class SteeringPolicy:
    display_name: str
    template: str  # only FAILOVER is supported
    ttl: int
    health_check_id: str | None
    answers: tuple


@dataclass(frozen=True)
class Snapshot:
    policies: tuple


def load_snapshot(path: str) -> Snapshot:
    with open(path, "r", encoding="utf-8") as fh:
        try:
            raw = json.load(fh)
        except json.JSONDecodeError as exc:
            raise SnapshotError(f"{path}: not valid JSON: {exc}") from exc
    if not isinstance(raw, dict) or not isinstance(raw.get("policies"), list):
        raise SnapshotError(f"{path}: top level must be an object with a 'policies' list")
    policies = []
    for i, p in enumerate(raw["policies"]):
        where = f"policies[{i}]"
        for req in ("display_name", "template", "ttl"):
            if req not in p:
                raise SnapshotError(f"{where}: missing required field {req!r}")
        if p["template"] != "FAILOVER":
            raise SnapshotError(f"{where}: unsupported template {p['template']!r} (only FAILOVER)")
        if not isinstance(p["ttl"], int) or p["ttl"] <= 0:
            raise SnapshotError(f"{where}: ttl must be a positive integer")
        answers = []
        for j, a in enumerate(p.get("answers", [])):
            awhere = f"{where}.answers[{j}]"
            for req in ("name", "pool", "priority", "rdata"):
                if req not in a:
                    raise SnapshotError(f"{awhere}: missing required field {req!r}")
            if not isinstance(a["priority"], int) or a["priority"] < 1:
                raise SnapshotError(f"{awhere}: priority must be a positive integer")
            answers.append(
                Answer(
                    name=a["name"],
                    pool=a["pool"],
                    priority=a["priority"],
                    enabled=bool(a.get("enabled", True)),
                    rdata=a["rdata"],
                )
            )
        policies.append(
            SteeringPolicy(
                display_name=p["display_name"],
                template=p["template"],
                ttl=p["ttl"],
                health_check_id=p.get("health_check_id"),
                answers=tuple(answers),
            )
        )
    return Snapshot(policies=tuple(policies))
