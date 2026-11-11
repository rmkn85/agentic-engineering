"""Check that normal entry routes reach the canonical architecture rule.

This proves navigation, not that a model follows the rule.
"""
from pathlib import Path
import re
import unittest


ROOT = Path(__file__).resolve().parents[2]


class ArchitectureEntryRoutes(unittest.TestCase):
    def test_default_and_adoption_entries_reach_the_same_rule(self):
        core = ROOT / "templates/contributor-core.md"
        heading = "Preserve architectural decisions"
        self.assertIn("## " + heading, core.read_text())
        for entry in (ROOT / "docs/agent-corpus/README.md", ROOT / "templates/AGENTS.md"):
            links = re.findall(r"\]\(([^)]+)\)", entry.read_text())
            targets = [(entry.parent / link.split("#")[0]).resolve() for link in links]
            self.assertIn(core, targets, entry.relative_to(ROOT))


if __name__ == "__main__":
    unittest.main()
