"""Check steering discovery and navigation, not agent behavior or effectiveness."""
from pathlib import Path
import re
import tempfile
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
SKILL = ROOT / 'skills/steering-delivery/SKILL.md'
GUIDE = ROOT / 'docs/execution/delivery-steering.md'
TRIAL = ROOT / 'experiments/delivery-steering.md'


def local_links(source: Path) -> set:
    """Resolve the simple inline Markdown links used in this guidance."""
    targets = set()
    for destination in re.findall(r'\[[^\]]*\]\(([^\s)]+)\)', source.read_text(encoding='utf-8')):
        parsed = urlsplit(destination)
        if not parsed.scheme and not parsed.netloc:
            target = source.parent / unquote(parsed.path) if parsed.path else source
            targets.add(target.resolve())
    return targets


def invalid_links(source: Path, root: Path) -> set:
    """Report missing or escaping local targets without opening those targets."""
    root = root.resolve()
    return {target for target in local_links(source)
            if root not in target.parents or not target.is_file()}


class DeliverySteeringNavigationTests(unittest.TestCase):
    def test_skill_discovery_metadata(self):
        text = SKILL.read_text(encoding='utf-8')
        self.assertTrue(text.startswith('---\n'))
        header = text.split('---', 2)[1]
        self.assertRegex(header, r'(?m)^name: steering-delivery$')
        self.assertRegex(header, r'(?m)^description: .+')

    def test_entry_and_workflow_routes_to_skill(self):
        for name in ('AGENTS.md', 'README.md', 'docs/agent-corpus/README.md',
                     'skills/README.md', 'skills/efficient-execution/SKILL.md',
                     'skills/recovering-interrupted-work/SKILL.md',
                     'docs/execution/direct-delivery.md', 'docs/adoption/overlays.md'):
            with self.subTest(entry=name):
                self.assertIn(SKILL, local_links(ROOT / name))

    def test_portable_core_names_skill_without_requiring_upstream(self):
        text = (ROOT / 'templates/contributor-core.md').read_text(encoding='utf-8')
        self.assertIn('`steering-delivery`', text)
        self.assertIn('fallback', text)
        self.assertNotIn('https://github.com/', text)

    def test_procedure_guide_and_trial_are_connected(self):
        self.assertIn(GUIDE, local_links(SKILL))
        self.assertIn(TRIAL, local_links(SKILL))
        self.assertIn(SKILL, local_links(GUIDE))
        self.assertIn(TRIAL, local_links(GUIDE))
        self.assertIn(SKILL, local_links(TRIAL))
        self.assertIn(GUIDE, local_links(TRIAL))
        protocol = ROOT / 'experiments/instruction-context-adherence.md'
        self.assertIn(protocol, local_links(TRIAL))

    def test_steering_resource_links_resolve_within_repository(self):
        for source in (SKILL, GUIDE, TRIAL):
            with self.subTest(source=str(source.relative_to(ROOT))):
                self.assertTrue(local_links(source))
                self.assertEqual(set(), invalid_links(source, ROOT))

    def test_navigation_check_detects_missing_target(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory).resolve()
            source = root / 'entry.md'
            source.write_text('[skill](missing/SKILL.md)\n', encoding='utf-8')
            self.assertEqual({root / 'missing/SKILL.md'}, invalid_links(source, root))
            (root / 'missing').mkdir()
            (root / 'missing/SKILL.md').write_text('# Skill\n', encoding='utf-8')
            self.assertEqual(set(), invalid_links(source, root))

    def test_navigation_check_detects_escaping_target(self):
        with tempfile.TemporaryDirectory() as directory:
            parent = Path(directory).resolve()
            root = parent / 'repo'
            root.mkdir()
            outside = parent / 'outside.md'
            outside.write_text('# Outside\n', encoding='utf-8')
            source = root / 'entry.md'
            source.write_text('[outside](../outside.md)\n', encoding='utf-8')
            self.assertEqual({outside}, invalid_links(source, root))


if __name__ == '__main__':
    unittest.main()
