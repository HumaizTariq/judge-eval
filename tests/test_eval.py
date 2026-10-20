import json
import os
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import run_eval  # noqa: E402
from variants import VARIANTS, flaw_named  # noqa: E402

# Path to the GTM agent; the agent tests skip when it is not set.
AGENT_DIR = Path(os.environ.get("GTM_AGENT_DIR", ROOT / "no-agent"))

PROFILE = {
    "name": "Acme", "domain": "acme.example", "what_they_do": "Sells widgets to plants.",
    "proof_points": ["Northwind cut downtime 20%."],
    "icp": {"industries": ["Manufacturing", "Logistics"], "company_size_range": "50-500",
            "geos": ["US"], "buyer_personas": ["VP Operations"],
            "qualifying_criteria": ["Runs a plant"], "disqualifiers": ["Under 10 staff"]},
}


class VariantTests(unittest.TestCase):
    def changed_keys(self, a, b, prefix=""):
        keys = set(a) | set(b)
        out = []
        for k in keys:
            if isinstance(a.get(k), dict):
                out += self.changed_keys(a[k], b[k], f"{prefix}{k}.")
            elif a.get(k) != b.get(k):
                out.append(prefix + k)
        return sorted(out)

    def test_each_variant_changes_only_its_field(self):
        expected = {
            "vague_icp": ["icp.company_size_range", "icp.industries"],
            "unsupported_proof": ["proof_points"],
            "marketing_copy": ["what_they_do"],
            "wrong_buyer": ["icp.buyer_personas"],
            "contradiction": ["icp.disqualifiers"],
        }
        for name, fn in VARIANTS.items():
            self.assertEqual(self.changed_keys(PROFILE, fn(PROFILE)), expected[name], name)
        self.assertEqual(PROFILE["icp"]["industries"], ["Manufacturing", "Logistics"])  # not mutated

    def test_contradiction_uses_own_industry(self):
        self.assertIn("Manufacturing companies", VARIANTS["contradiction"](PROFILE)["icp"]["disqualifiers"])

    def test_flaw_named(self):
        self.assertTrue(flaw_named("wrong_buyer", ["Buyer personas don't match the product"]))
        self.assertFalse(flaw_named("wrong_buyer", ["Looks fine"]))
        self.assertFalse(flaw_named("", ["anything"]))


class ReportTests(unittest.TestCase):
    def test_summarize(self):
        vs = [{"deliverable": "base", "variant": "", "score": s, "approved": s >= 7, "issues": []}
              for s in (8, 8, 6)]
        vs += [{"deliverable": "v", "variant": "wrong_buyer", "score": 4, "approved": False,
                "issues": ["wrong persona"]},
               {"deliverable": "v", "variant": "wrong_buyer", "score": 8, "approved": True,
                "issues": []}]
        rows = run_eval.summarize(vs)
        self.assertEqual(rows[0], {"deliverable": "base", "variant": "", "n": 3, "mean": 7.33,
                                   "min": 6, "max": 8, "stdev": 0.94, "approved": 2})
        self.assertEqual((rows[1]["flaw_named"], rows[1]["approved"]), (1, 1))
        md = run_eval.report_md(rows, 0.1234, 5)
        self.assertIn("| base | 6-8 | 7.33 | 0.94 | 2/3 | - |", md)
        self.assertIn("| v | 4-8 | 6.0 | 2.0 | 1/2 | 1/2 |", md)


@unittest.skipUnless((AGENT_DIR / "src/gtm_engineer/main.py").is_file(), "agent not present")
class AgentPromptTests(unittest.TestCase):
    def test_prompt_copy_matches_agent_source(self):
        src = (AGENT_DIR / "src/gtm_engineer/main.py").read_text(encoding="utf-8")
        # The fixed text before each placeholder, as it is written in source (\n escaped).
        for line in run_eval.PROMPT_LINES:
            piece = json.dumps(line.split("{")[0])[1:-1]
            self.assertIn(piece, src)
        self.assertIn("For research: ICPs must name real industries/sizes/titles and ", src)
        self.assertIn("personalization angles must cite concrete facts.", src)

    def test_plan_has_seven_deliverables(self):
        self.assertEqual(len(run_eval.load_deliverables(AGENT_DIR)), 7)


if __name__ == "__main__":
    unittest.main()
