import io
import os
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from dns_failover.cli import main

SAMPLES = os.path.join(os.path.dirname(__file__), "..", "samples")


class TestCli(unittest.TestCase):
    def run_cli(self, argv):
        out, err = io.StringIO(), io.StringIO()
        with redirect_stdout(out), redirect_stderr(err):
            code = main(argv)
        return code, out.getvalue(), err.getvalue()

    def test_messy_sample_exits_2_and_covers_rules(self):
        code, out, _ = self.run_cli([os.path.join(SAMPLES, "policies_messy.json")])
        self.assertEqual(code, 2)
        for rule in ("DNS001", "DNS002", "DNS003", "DNS004"):
            self.assertIn(rule, out)

    def test_clean_sample_exits_0(self):
        code, out, _ = self.run_cli([os.path.join(SAMPLES, "policies_clean.json")])
        self.assertEqual(code, 0)
        self.assertIn("RESULT: clean", out)

    def test_non_failover_template_exits_2(self):
        doc = '{"policies": [{"display_name": "x", "template": "LOAD_BALANCE", "ttl": 60}]}'
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            fh.write(doc)
            path = fh.name
        try:
            code, _, err = self.run_cli([path])
            self.assertEqual(code, 2)
            self.assertIn("unsupported template", err)
        finally:
            os.unlink(path)

    def test_bad_priority_exits_2(self):
        doc = '{"policies": [{"display_name": "x", "template": "FAILOVER", "ttl": 60, "answers": [{"name": "a", "pool": "p", "priority": 0, "rdata": "1.1.1.1"}]}]}'
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as fh:
            fh.write(doc)
            path = fh.name
        try:
            code, _, err = self.run_cli([path])
            self.assertEqual(code, 2)
            self.assertIn("priority", err)
        finally:
            os.unlink(path)


if __name__ == "__main__":
    unittest.main()
