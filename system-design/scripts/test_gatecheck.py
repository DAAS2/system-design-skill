"""Golden tests for gatecheck.py. Run: python -m unittest test_gatecheck -v"""

import unittest

import gatecheck

PASSING_DOC = """# Design: Example widget service

## Non-goals
- No multi-region. - No custom aliases. - No per-item analytics.

## Capacity
```
$ python botec.py full --dau 50000 --reads-per-user 20 --writes-per-user 2
Read QPS avg / peak ................ 11.6 / 23.1
```

## Failure modes
| # | Injection | Behavior | Mechanism | Residual risk |
|---|---|---|---|---|
| 1 | Dependency down | degrade | fallback cache | pager |
| 2 | 10x spike | survive | autoscale x2 | cost |
| 3 | Hot key | degrade | salted keys | none |
| 4 | Cache stampede | survive | single-flight | none |
| 5 | Retry storm | survive | jittered backoff | none |
| 6 | Split-brain | n/a | single writer | none |
| 7 | Poison message | survive | DLQ + alarm | ops |
| 8 | Slow consumer | degrade | bounded queue | lag |
| 9 | Region loss | die, accepted | RPO 15 min | redesign note |
| 10 | Clock skew | survive | monotonic IDs | none |
| 11 | Cascading failure | survive | bulkheads | none |
| 12 | Metastable failure | degrade | load-shed | runbook |

## Right-sizing & cost
- Tier: 1 because 50k users/day sits in the traction band.
- Estimated monthly cost: $210/mo (2 nodes, managed Postgres, Redis)
- cost per 1k requests: $0.004

## Evolution
- Breaks first at 10x: the single Postgres primary
- Next step at 10x: read replicas before partitioning
"""


class TestGatecheck(unittest.TestCase):
    def setUp(self):
        self.results = {r["id"]: r for r in gatecheck.check_document(PASSING_DOC)}

    def test_passing_doc_passes_every_check(self):
        results = gatecheck.check_document(PASSING_DOC)
        failed = [r["id"] for r in results if not r["ok"]]
        self.assertEqual(failed, [], f"expected all checks to pass, failed: {failed}")

    def test_all_seven_checks_present(self):
        self.assertEqual(
            set(self.results),
            {"capacity", "failure-table", "tier", "cost-monthly", "cost-per-1k", "non-goals", "evolution"},
        )

    def test_missing_botec_and_qps_fails_capacity(self):
        doc = PASSING_DOC.replace("botec.py full", "estimate.py").replace("QPS avg / peak", "throughput 500/s")
        doc = doc.replace("botec", "calculator")
        results = {r["id"]: r for r in gatecheck.check_document(doc)}
        self.assertFalse(results["capacity"]["ok"])

    def test_incomplete_failure_table_fails(self):
        doc = PASSING_DOC.replace("| 12 | Metastable failure | degrade | load-shed | runbook |\n", "")
        results = {r["id"]: r for r in gatecheck.check_document(doc)}
        self.assertFalse(results["failure-table"]["ok"])
        self.assertIn("11/12", results["failure-table"]["detail"])

    def test_missing_tier_fails(self):
        doc = PASSING_DOC.replace("- Tier: 1 because 50k users/day sits in the traction band.", "")
        results = {r["id"]: r for r in gatecheck.check_document(doc)}
        self.assertFalse(results["tier"]["ok"])

    def test_missing_monthly_cost_fails(self):
        doc = PASSING_DOC.replace("- Estimated monthly cost: $210/mo (2 nodes, managed Postgres, Redis)", "")
        results = {r["id"]: r for r in gatecheck.check_document(doc)}
        self.assertFalse(results["cost-monthly"]["ok"])

    def test_missing_per_1k_fails(self):
        doc = PASSING_DOC.replace("- cost per 1k requests: $0.004", "")
        results = {r["id"]: r for r in gatecheck.check_document(doc)}
        self.assertFalse(results["cost-per-1k"]["ok"])

    def test_missing_non_goals_fails(self):
        doc = PASSING_DOC.replace("## Non-goals", "## Scope notes").replace("No multi-region.", "")
        results = {r["id"]: r for r in gatecheck.check_document(doc)}
        self.assertFalse(results["non-goals"]["ok"])

    def test_missing_evolution_fails(self):
        doc = PASSING_DOC.replace("- Breaks first at 10x: the single Postgres primary\n", "")
        doc = doc.replace("- Next step at 10x: read replicas before partitioning\n", "")
        doc = doc.replace("## Evolution", "## Later")
        results = {r["id"]: r for r in gatecheck.check_document(doc)}
        self.assertFalse(results["evolution"]["ok"])

    def test_sections_parser_splits_on_headings(self):
        secs = gatecheck.sections(PASSING_DOC)
        self.assertIn("failure modes", secs)
        self.assertIn("non-goals", secs)
        self.assertIn("10x", secs["evolution"])

    def test_teardown_docs_are_skipped_not_failed(self):
        self.assertTrue(gatecheck.is_comparison_doc(
            "# The design griller\n\n## What the baseline agent built (excerpts)\n"
            "## What the skill produced (excerpts)\n## The tear-down\n"))
        self.assertFalse(gatecheck.is_comparison_doc(PASSING_DOC))


if __name__ == "__main__":
    unittest.main()
