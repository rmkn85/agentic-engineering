"""Check guidance navigation only, not agent adherence or product accessibility."""
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
CONTRACT = ROOT / 'docs/interfaces/accessible-interfaces.md'
STANDARDS = ROOT / 'docs/interfaces/standards.md'


def local_links(source: Path) -> set:
    """Resolve simple inline Markdown links used by these guidance documents."""
    targets = set()
    for destination in re.findall(r'\[[^\]]*\]\(([^\s)]+)\)', source.read_text(encoding='utf-8')):
        parsed = urlsplit(destination)
        if not parsed.scheme and not parsed.netloc:
            target = source.parent / unquote(parsed.path) if parsed.path else source
            targets.add(target.resolve())
    return targets


class InterfaceGuidanceNavigationTests(unittest.TestCase):
    def test_normal_entry_routes_to_contract(self):
        for name in ('AGENTS.md', 'docs/agent-corpus/README.md'):
            with self.subTest(entry=name):
                self.assertIn(CONTRACT, local_links(ROOT / name))

    def test_adoption_validation_and_index_route_to_contract(self):
        for name in ('docs/adoption/newcomer-contract.md',
                     'docs/runtime/e2e-readiness.md', 'docs/README.md'):
            with self.subTest(entry=name):
                self.assertIn(CONTRACT, local_links(ROOT / name))

    def test_contract_and_standards_link_each_other(self):
        self.assertIn(STANDARDS, local_links(CONTRACT))
        self.assertIn(CONTRACT, local_links(STANDARDS))

    def test_interface_document_local_links_resolve_within_repo(self):
        for source in (CONTRACT, STANDARDS):
            targets = local_links(source)
            self.assertTrue(targets, f'No local links found in {source.name}')
            for target in targets:
                with self.subTest(source=source.name, target=str(target)):
                    self.assertIn(ROOT, target.parents)
                    self.assertTrue(target.is_file(), f'Missing guidance target: {target}')


if __name__ == '__main__':
    unittest.main()
