import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOLS = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(TOOLS))
import blind_review
import check_review


class ReviewBoundaryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        subprocess.run(['git', 'init', '-q', str(self.root)], check=True)
        (self.root / 'tools').mkdir()
        (self.root / 'tools/finish_check.py').write_text('original instructions')
        for args in [('add', '.'), ('-c', 'user.name=Fixture', '-c', 'user.email=fixture@example.invalid',
                                   'commit', '-qm', 'baseline')]:
            subprocess.run(['git', *args], cwd=self.root, check=True)
        (self.root / 'tools/finish_check.py').write_text('changed instructions')

    def review(self):
        folder = self.root / 'validation/reviews'; folder.mkdir(parents=True)
        for name, text in [('request.md', 'Deliver the complete consumer outcome'),
                           ('failure.md', 'The consumer check failed despite internal success'),
                           ('report.md', 'Reviewed the request and checked the changed behavior')]:
            (folder / name).write_text(text)
        criteria = folder / 'criteria.json'
        criteria.write_text(json.dumps({'criteria': [{'id': 'consumer', 'requirement': 'Consumer works',
                                                      'check': 'Independent consumer check'}], 'discrepancies': []}))
        blind_review.seal_frame(folder/'request.md', folder/'failure.md', criteria, folder/'frame.json')
        record = {'schema': 'methodology-review/v1', 'framing': 'validation/reviews/frame.json',
                  'request': 'validation/reviews/request.md', 'failure_evidence': 'validation/reviews/failure.md',
                  'verdict': 'accepted', 'report': {'path': 'validation/reviews/report.md',
                  'sha256': check_review.identity(self.root, 'validation/reviews/report.md')},
                  'files': {'tools/finish_check.py': check_review.identity(self.root, 'tools/finish_check.py')}}
        record['input_hashes'] = {key: check_review.identity(self.root, record[key])
                                  for key in ('framing', 'request', 'failure_evidence')}
        (folder/'manifest.json').write_text(json.dumps(record))

    def test_changed_controls_require_review(self):
        self.assertTrue(check_review.check(self.root, 'HEAD'))
        self.review()
        self.assertEqual(check_review.check(self.root, 'HEAD'), [])

    def test_changed_source_or_report_invalidates_review(self):
        self.review()
        (self.root/'tools/finish_check.py').write_text('unreviewed follow-up')
        self.assertTrue(check_review.check(self.root, 'HEAD'))
        (self.root/'validation/reviews/report.md').write_text('withdrawn')
        self.assertTrue(check_review.check(self.root, 'HEAD'))

    def test_no_methodology_change_needs_no_review(self):
        (self.root/'tools/finish_check.py').write_text('original instructions')
        (self.root/'product.txt').write_text('small product change')
        self.assertEqual(check_review.check(self.root, 'HEAD'), [])

    def test_resealing_changed_request_cannot_reuse_accepted_report(self):
        self.review()
        folder = self.root / 'validation/reviews'
        (folder / 'request.md').write_text('A different request with different acceptance')
        (folder / 'frame.json').unlink()
        blind_review.seal_frame(folder/'request.md', folder/'failure.md', folder/'criteria.json', folder/'frame.json')
        errors = check_review.check(self.root, 'HEAD')
        self.assertTrue(any('framing inputs changed' in error for error in errors))

    def test_gates_evaluators_and_ci_routes_need_review(self):
        (self.root/'tools/finish_check.py').write_text('original instructions')
        for name in ('tools/make', 'tools/work_audit.py', 'validation/trials/recurrence/score.py',
                     '.github/workflows/verify.yml', '.claude/settings.json', '.codex/hooks.json',
                     'configs/guidance-budget.json', 'configs/allowed-activities.json', '.agent/audit.json',
                     'tools/check-outcome-controls.py', 'tools/check_hygiene.py', 'tools/check-fresh.py'):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('changed control')
            self.assertTrue(any(name in error for error in check_review.check(self.root, 'HEAD')))

    def test_guidance_ordinary_tools_and_evidence_need_no_receipt(self):
        (self.root/'tools/finish_check.py').write_text('original instructions')
        for name in ('AGENTS.md', 'docs/execution/control.md', 'skills/x/SKILL.md', 'tools/repo-index.py',
                     'validation/trials/recurrence/results.jsonl'):
            path = self.root / name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text('changed guidance')
        self.assertEqual(check_review.check(self.root, 'HEAD'), [])

if __name__ == '__main__':
    unittest.main()
