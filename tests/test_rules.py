import unittest

from dns_failover.model import Answer, Snapshot, SteeringPolicy
from dns_failover.rules import (
    exit_code,
    rule_empty_pool,
    rule_long_ttl,
    rule_no_health_check,
    rule_priority_gaps,
    run_all,
)


def ans(pool="primary", prio=1, enabled=True, name=None):
    return Answer(name=name or f"{pool}-{prio}", pool=pool, priority=prio, enabled=enabled, rdata="192.0.2.1")


def policy(answers=(), ttl=60, hc="hc1", name="p1"):
    return SteeringPolicy(display_name=name, template="FAILOVER", ttl=ttl,
                          health_check_id=hc, answers=tuple(answers))


class TestDns001EmptyPool(unittest.TestCase):
    def test_fires_when_pool_all_disabled(self):
        snap = Snapshot(policies=(policy(answers=[ans(), ans(pool="backup", prio=2, enabled=False)]),))
        out = rule_empty_pool(snap)
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].severity, "HIGH")
        self.assertIn("backup", out[0].detail)

    def test_quiet_when_every_pool_enabled(self):
        snap = Snapshot(policies=(policy(answers=[ans(), ans(pool="backup", prio=2)]),))
        self.assertEqual(rule_empty_pool(snap), [])


class TestDns002PriorityGaps(unittest.TestCase):
    def test_fires_on_gap(self):
        snap = Snapshot(policies=(policy(answers=[ans(prio=1), ans(pool="backup", prio=3)]),))
        self.assertEqual(len(rule_priority_gaps(snap)), 1)

    def test_fires_on_duplicate(self):
        snap = Snapshot(policies=(policy(answers=[ans(prio=1), ans(pool="backup", prio=1)]),))
        self.assertEqual(len(rule_priority_gaps(snap)), 1)

    def test_contiguous_is_clean(self):
        snap = Snapshot(policies=(policy(answers=[ans(prio=1), ans(pool="backup", prio=2)]),))
        self.assertEqual(rule_priority_gaps(snap), [])

    def test_disabled_answers_ignored(self):
        snap = Snapshot(policies=(policy(answers=[ans(prio=1), ans(pool="backup", prio=9, enabled=False)]),))
        # only one enabled answer -> priorities [1] -> clean
        self.assertEqual(rule_priority_gaps(snap), [])


class TestDns003HealthCheck(unittest.TestCase):
    def test_fires_without_health_check(self):
        snap = Snapshot(policies=(policy(hc=None, answers=[ans()]),))
        self.assertEqual(len(rule_no_health_check(snap)), 1)

    def test_quiet_with_health_check(self):
        snap = Snapshot(policies=(policy(answers=[ans()]),))
        self.assertEqual(rule_no_health_check(snap), [])


class TestDns004Ttl(unittest.TestCase):
    def test_fires_over_300(self):
        snap = Snapshot(policies=(policy(ttl=3600, answers=[ans()]),))
        self.assertEqual(len(rule_long_ttl(snap)), 1)

    def test_boundary_300_is_ok(self):
        snap = Snapshot(policies=(policy(ttl=300, answers=[ans()]),))
        self.assertEqual(rule_long_ttl(snap), [])


class TestAggregation(unittest.TestCase):
    def test_exit_code_2_on_high(self):
        snap = Snapshot(policies=(policy(answers=[ans(pool="dead", prio=1, enabled=False)]),))
        self.assertEqual(exit_code(run_all(snap)), 2)

    def test_exit_code_1_on_medium_only(self):
        snap = Snapshot(policies=(policy(hc=None, answers=[ans()]),))
        self.assertEqual(exit_code(run_all(snap)), 1)

    def test_exit_code_0_when_clean(self):
        snap = Snapshot(policies=(policy(answers=[ans(), ans(pool="backup", prio=2)]),))
        self.assertEqual(exit_code(run_all(snap)), 0)

    def test_sorted_high_first(self):
        snap = Snapshot(policies=(policy(ttl=3600, hc=None,
                                         answers=[ans(pool="dead", prio=1, enabled=False)]),))
        findings = run_all(snap)
        self.assertEqual(findings[0].severity, "HIGH")
        self.assertEqual(findings[-1].severity, "LOW")


if __name__ == "__main__":
    unittest.main()
