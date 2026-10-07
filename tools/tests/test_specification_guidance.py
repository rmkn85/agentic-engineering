"""Offline navigation checks, not STE compliance or agent-behavior tests.

The parser handles this corpus's inline links and ATX headings, not all Markdown.
"""
from pathlib import Path
import re
import unittest
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[2]
SPEC = 'docs/specifications/README.md'
LANGUAGE = 'docs/specifications/technical-language.md'
STANDARDS = 'docs/specifications/standards.md'
MIGRATION = 'docs/adoption/standards-migration.md'
EXPERIMENT = 'experiments/specification-integrity.md'
NEW_DOCS = (SPEC, LANGUAGE, STANDARDS, MIGRATION, EXPERIMENT)
ROUTES = {
    'AGENTS.md': (SPEC, LANGUAGE, MIGRATION),
    'docs/agent-corpus/README.md': (SPEC, LANGUAGE, STANDARDS, MIGRATION),
    'docs/adoption/newcomer-contract.md': (SPEC, MIGRATION, EXPERIMENT),
    'skills/improving-execution-guidance/SKILL.md': (SPEC, LANGUAGE, MIGRATION),
    'docs/README.md': NEW_DOCS,
}


def prose_lines(text: str) -> list[str]:
    """Ignore fenced examples so their sample paths do not become navigation."""
    result = []
    fence = None
    for line in text.splitlines():
        marker = re.match(r'^\s*(`{3,}|~{3,})', line)
        if marker:
            token = marker.group(1)
            if fence is None:
                fence = token
            elif token[0] == fence[0] and len(token) >= len(fence):
                fence = None
            continue
        if fence is None:
            result.append(line)
    if fence is not None:
        raise ValueError('Unclosed Markdown fence')
    return result


def local_links(source: Path, text: str, root: Path) -> set[tuple[Path, str]]:
    result = set()
    body = '\n'.join(prose_lines(text))
    for href in re.findall(r'\[[^\]]+\]\(([^\s()]+)\)', body):
        parts = urlsplit(href)
        if parts.scheme or parts.netloc:
            continue
        target = (source.parent / unquote(parts.path)).resolve() if parts.path else source.resolve()
        target.relative_to(root.resolve())  # Reject paths escaping the repository.
        result.add((target, unquote(parts.fragment)))
    return result


def heading_ids(text: str) -> set[str]:
    result = set()
    for line in prose_lines(text):
        match = re.match(r'^#{1,6}\s+(.+?)\s*#*$', line)
        if match:
            stem = re.sub(r'[^\w -]', '', match.group(1).lower()).replace(' ', '-')
            anchor, suffix = stem, 0
            while anchor in result:
                suffix += 1
                anchor = f'{stem}-{suffix}'
            result.add(anchor)
    return result


class MarkdownNavigationHelperTests(unittest.TestCase):
    def test_examples_and_external_urls_are_not_local_navigation(self):
        root = Path('/virtual-repository')
        text = ('[Real](docs/guide.md#start)\n[External](https://example.org/a)\n'
                '```text\n[Example](missing.md)\n```\n')
        self.assertEqual(local_links(root / 'AGENTS.md', text, root),
                         {(root / 'docs/guide.md', 'start')})

    def test_unclosed_fence_is_rejected(self):
        with self.assertRaises(ValueError):
            prose_lines('```text\nunfinished')

    def test_repository_escape_is_rejected(self):
        root = Path('/virtual-repository')
        with self.assertRaises(ValueError):
            local_links(root / 'AGENTS.md', '[Escape](../outside.md)', root)

    def test_headings_preserve_distinct_anchors(self):
        text = "# Start\n## Start\n## The implementation's story\n```\n# Hidden\n```\n"
        self.assertEqual(heading_ids(text), {'start', 'start-1', 'the-implementations-story'})


class SpecificationGuidanceNavigationTests(unittest.TestCase):
    def assert_route(self, entry: str, targets: tuple[str, ...]) -> None:
        source = ROOT / entry
        links = local_links(source, source.read_text(encoding='utf-8'), ROOT)
        paths = {path for path, _ in links}
        for target in targets:
            with self.subTest(entry=entry, target=target):
                self.assertIn(ROOT / target, paths)
                self.assertTrue((ROOT / target).is_file())

    def test_normal_entries_route_to_specification_and_migration(self):
        for entry in ('AGENTS.md', 'docs/agent-corpus/README.md'):
            self.assert_route(entry, ROUTES[entry])

    def test_adoption_and_improvement_routes(self):
        for entry in ('docs/adoption/newcomer-contract.md',
                      'skills/improving-execution-guidance/SKILL.md'):
            self.assert_route(entry, ROUTES[entry])

    def test_documentation_index_routes(self):
        self.assert_route('docs/README.md', ROUTES['docs/README.md'])

    def test_new_document_links_and_anchors_resolve(self):
        for name in NEW_DOCS:
            source = ROOT / name
            text = source.read_text(encoding='utf-8')
            links = local_links(source, text, ROOT)
            self.assertTrue(links, f'No local routes in {name}')
            for target, anchor in links:
                with self.subTest(source=name, target=str(target), anchor=anchor):
                    self.assertTrue(target.is_file(), f'Missing target: {target}')
                    if anchor:
                        self.assertIn(anchor, heading_ids(target.read_text(encoding='utf-8')))

    def test_entry_links_to_new_contract_anchors_resolve(self):
        targets = {ROOT / name for name in NEW_DOCS}
        for entry in ROUTES:
            source = ROOT / entry
            for target, anchor in local_links(source, source.read_text(encoding='utf-8'), ROOT):
                if target in targets and anchor:
                    with self.subTest(entry=entry, target=str(target), anchor=anchor):
                        self.assertIn(anchor, heading_ids(target.read_text(encoding='utf-8')))

    def test_new_documents_have_clean_whitespace(self):
        for name in NEW_DOCS:
            text = (ROOT / name).read_text(encoding='utf-8')
            with self.subTest(document=name):
                self.assertTrue(text.endswith('\n'))
                self.assertFalse(any(line.rstrip() != line for line in text.splitlines()))


if __name__ == '__main__':
    unittest.main()
