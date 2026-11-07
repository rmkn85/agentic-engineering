"""Obligations a rewrite of AGENTS.md must not drop silently.

Each entry is an obligation from the guidance, with a pattern that must still
match. Removing one is allowed only by removing it here too, in the same
change, where a reviewer sees it.
"""
from pathlib import Path
import re
import unittest


AGENTS = Path(__file__).resolve().parents[2] / "AGENTS.md"
OBLIGATIONS = {
    "goal record first": r"\.agent/goal\.json",
    "finish through the gate": r"make finish-check",
    "never weaken acceptance": r"never invent requirements or weaken acceptance",
    "migrate existing work": r"existing or active work.*standards migration",
    "sandbox first, external effects last": r"external effects last",
    "no equivalent access elsewhere": r"never seek equivalent access",
    "reuse needs authority": r"reusing a worker still needs compliant configuration and authority",
    "workload-dependent benchmarking": r"workload-dependent deviations",
    "escalate to an authorized coordinator": r"more capable authorized coordinator",
    "no worker above its ceiling": r"never a worker above its ceiling",
    "report unrun checks": r"Report unrun checks",
    "no executable work as next steps": r"Never present executable required work as \"next steps\"",
    "guidance changes need evidence": r"add or change a test that fails",
    "budgets only go down": r"Budgets only go down",
    "no private content": r"Never copy private repository content",
}


class AgentsObligationTests(unittest.TestCase):
    def test_every_obligation_is_still_stated(self):
        text = " ".join(AGENTS.read_text(encoding="utf-8").split())
        for name, pattern in OBLIGATIONS.items():
            with self.subTest(obligation=name):
                self.assertRegex(text, pattern)


if __name__ == "__main__":
    unittest.main()
