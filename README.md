# oci-ootb-dns-failover-policy-check

**Category: OOTB project - built from named built-in OCI services.** The *custom portfolio tool*
in this daily pair is `oci-logging-coverage-audit`; this repo is the one that wires native
platform services.

## Built-in OCI services wired

**OCI DNS Traffic Management** (steering policies) **+ OCI Health Checks** (HTTP monitors).
`terraform/` declares the native service configuration:

- `oci_health_checks_http_monitor` - probes the primary endpoint so DNS knows when it is sick
- `oci_dns_steering_policy` - a `FAILOVER` template policy: answers ordered by pool/priority
- `oci_dns_steering_policy_attachment` - binds the policy to the DNS zone

That is the "OOTB" part: the health probing, answer selection and failover itself are native OCI
capabilities, not code written here.

## Custom code (what this repo adds)

DNS failover looks simple until a pool is empty, priorities collide, or the policy was never
attached to a health check - then the first real outage exposes it. `dns_failover/` is a custom
Python checker that reads an **offline snapshot** of steering policies and applies four rules:

| Rule | Severity | Fires when |
| ---- | -------- | ---------- |
| DNS001 | HIGH | A pool in the failover chain has zero enabled answers - if traffic ever fails over to it, there is nothing to serve. |
| DNS002 | MEDIUM | Priorities within a policy are not 1,2,3,... - gaps or duplicates make failover order ambiguous. |
| DNS003 | MEDIUM | The policy has no health check attached - failover runs blind to endpoint health. |
| DNS004 | LOW | TTL above 300s - clients cache the dying endpoint too long during a failover. |

Exit code: `2` if any HIGH finding, `1` if only MEDIUM/LOW, `0` when clean.

## Run it

```bash
python -m dns_failover.cli samples/policies_messy.json   # exits 2, all 4 rules fire
python -m dns_failover.cli samples/policies_clean.json   # exits 0
```

## Test it

```bash
python -m unittest discover -s tests -v   # stdlib only
```

## What actually ran vs template-only

- **Ran (locally + CI):** the Python checker - unit tests green on Python 3.10/3.11/3.12, and both
  demo invocations above execute as CI steps with asserted exit codes.
- **Template-only:** the Terraform in `terraform/` is **NOT plan/apply validated** - no zone was
  touched, no steering policy, health check or attachment was created, and no DNS failover was
  actually exercised. It is the native-service wiring the checker would validate in a real
  deployment.
- The sample policy JSON is synthetic; no live zone data is included.

## Honest limits

- Offline check of a static snapshot; it does not call the OCI DNS or Health Checks APIs.
- FAILOVER template only - LOAD_BALANCE / GEOLOCATION / ASN steering rules are out of scope.
- Priority contiguity (DNS002) assumes one answer set per policy; pool-weighted variants would
  need a relaxed check.
- DNS001 means "this pool cannot serve as configured" - it is a config finding, not a claim that
  failover is currently happening.

## Layout

```
dns_failover/   custom Python: model, rules, CLI
terraform/      OCI Health Checks monitor + DNS steering policy + attachment (NOT plan/apply validated)
samples/        synthetic policy snapshots
tests/          stdlib unit tests
```

No paid services, no live cloud calls, no accounts created.
