"""Behavioral task contract and real HTTP boundary regression tests."""
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from urllib.error import HTTPError
from urllib.request import Request, urlopen

TOOL = Path(__file__).resolve().parents[1] / 'project_work.py'
spec = importlib.util.spec_from_file_location('project_work', TOOL)
work = importlib.util.module_from_spec(spec)
spec.loader.exec_module(work)


def task(task_id='RUN-001', status='planned', depends=None):
    return {'schema': work.TASK_SCHEMA, 'id': task_id, 'title': 'A useful outcome',
            'status': status, 'outcome': 'An independently observable result',
            'depends': depends or [], 'acceptance': ['The consumer sees the result'],
            'evidence': ['A retained observation'], 'current': {
                'summary': 'Current state', 'nextAction': 'Exercise the consumer', 'blockers': []}}


class ProjectWorkTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.workspace = Path(self.temp.name)
        self.root = self.repository('one', 'sample/one')

    def repository(self, directory, name, lifecycle='active'):
        root = self.workspace / directory
        (root / '.git').mkdir(parents=True)
        (root / 'work/tasks').mkdir(parents=True)
        (root / 'work/frontier.json').write_text(json.dumps({
            'schema': work.FRONTIER_SCHEMA, 'repository': name, 'objective': 'Deliver an outcome',
            'mode': 'product', 'product': ['RUN-001'], 'maintenance': [], 'parallel': [],
            'lifecycle': lifecycle, 'projectExtension': {'preserved': True}}))
        self.write_task(task(), root)
        return root

    def write_task(self, data, root=None, filename=None):
        root = root or self.root
        (root / 'work/tasks' / (filename or data['id'] + '.json')).write_text(json.dumps(data))

    def state(self):
        return work.snapshot(work.discover(self.workspace))

    def test_dependency_resolution_and_queue_are_distinct_from_readiness(self):
        self.write_task(task(depends=['RUN-002', 'sample/two#RUN-001']))
        self.write_task(task('RUN-002', 'done'))
        state = self.state()
        row = work.overview(state)['tasks'][0]
        self.assertEqual(row['queue'], [{'repository': 'sample/one', 'lane': 'product', 'position': 1}])
        self.assertFalse(row['ready'])
        self.assertEqual(row['dependencies'][1]['state'], 'unavailable')
        two = self.repository('two', 'sample/two')
        self.write_task(task(status='done'), two)
        self.assertTrue(work.overview(self.state(), repository='sample/one')['tasks'][0]['ready'])
        self.write_task(task('RUN-002', 'in-progress'))
        self.assertFalse(work.overview(self.state(), repository='sample/one')['tasks'][0]['ready'])

    def test_resolved_blocker_records_keep_evidence_without_preventing_readiness(self):
        data = task()
        data['current']['blockers'] = [
            {'id': 'B1', 'disposition': 'resolved', 'observed': 'Previously unavailable',
             'sources': [{'path': 'retained-observation.log'}], 'exit': 'Consumer succeeds'},
            {'id': 'B2', 'disposition': 'superseded', 'nextAction': 'Use replacement record'}]
        self.write_task(data)
        state = self.state()
        row = work.overview(state)['tasks'][0]
        self.assertTrue(row['ready'])
        self.assertEqual(row['activeBlockerCount'], 0)
        self.assertEqual(len(row['current']['blockers']), 2)
        self.assertEqual(work.task_detail(state, 'sample/one', 'RUN-001')['current']['blockers'],
                         data['current']['blockers'])
        for active in ('A current obstruction', {'observed': 'No disposition'},
                       {'disposition': 'open'}, {'disposition': 'unknown'}):
            with self.subTest(active=active):
                data['current']['blockers'].append(active)
                self.write_task(data)
                row = work.overview(self.state())['tasks'][0]
                self.assertFalse(row['ready'])
                self.assertEqual(row['activeBlockerCount'], 1)
                data['current']['blockers'].pop()

    def test_default_current_queue_excludes_unchanged_outside_records(self):
        self.write_task(task('OLD-001', 'in-progress'))
        self.write_task(task('LATER-001', 'planned'))
        self.write_task(task('FINISHED-001', 'done'))
        state = self.state()
        self.assertEqual([row['id'] for row in work.overview(state)['tasks']], ['RUN-001'])
        all_rows = work.overview(state, scope='all')['tasks']
        self.assertEqual(len(all_rows), 4)
        self.assertEqual(work.overview(state, status='done')['total'], 0)
        self.assertEqual(work.overview(state, status='done', scope='all')['total'], 1)
        outside = next(row for row in all_rows if row['id'] == 'LATER-001')
        self.assertFalse(outside['queued'])
        self.assertFalse(outside['ready'])
        self.assertEqual(outside['status'], 'planned')
        self.assertEqual(work.task_detail(state, 'sample/one', 'OLD-001')['status'], 'in-progress')

    def test_done_transitive_open_prerequisite_is_not_ready(self):
        self.write_task(task(depends=['RUN-002']))
        self.write_task(task('RUN-002', 'done', ['RUN-003']))
        self.write_task(task('RUN-003', 'blocked'))
        row = next(row for row in work.overview(self.state())['tasks'] if row['id'] == 'RUN-001')
        self.assertFalse(row['ready'])
        self.assertEqual(row['dependencies'][0]['state'], 'prerequisites-open')

    def test_validation_rejects_defects_without_requiring_every_task_in_queue(self):
        self.write_task(task('RUN-002'))
        self.assertEqual(work.load_repository(self.root)['errors'], [])
        self.write_task(task('RUN-002'), filename='duplicate.json')
        errors = work.load_repository(self.root)['errors']
        self.assertTrue(any('duplicate task id' in error for error in errors))
        bad = task('BAD', depends=['ABSENT'])
        self.write_task(bad)
        self.assertTrue(any('unresolved local dependency' in error for error in work.load_repository(self.root)['errors']))
        bad['status'] = 'finished'
        bad['current']['nextAction'] = 1
        self.assertIn('invalid status', work.task_errors(bad))
        self.assertIn('current.nextAction must be a string', work.task_errors(bad))

    def test_build_is_deterministic_preserves_records_and_does_not_rewrite(self):
        original = (self.root / 'work/frontier.json').read_bytes()
        command = [sys.executable, str(TOOL), '--root', str(self.root), 'build']
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
        now = self.root / 'work/NOW.md'
        before = now.stat().st_mtime_ns
        self.assertIn('RUN-001', now.read_text())
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
        self.assertEqual(now.stat().st_mtime_ns, before)
        self.assertEqual((self.root / 'work/frontier.json').read_bytes(), original)

    def test_build_check_missing_current_stale_without_writes(self):
        command = [sys.executable, str(TOOL), '--root', str(self.root), 'build']
        now = self.root / 'work/NOW.md'
        before = sorted(path.relative_to(self.root) for path in self.root.rglob('*'))
        missing = subprocess.run(command + ['--check'], capture_output=True, text=True)
        self.assertNotEqual(missing.returncode, 0)
        self.assertIn('stale or missing', missing.stderr)
        self.assertEqual(before, sorted(path.relative_to(self.root) for path in self.root.rglob('*')))
        self.assertFalse(now.exists())
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
        content, modified = now.read_bytes(), now.stat().st_mtime_ns
        self.assertEqual(subprocess.run(command + ['--check'], capture_output=True).returncode, 0)
        self.assertEqual((now.read_bytes(), now.stat().st_mtime_ns), (content, modified))
        changed = task()
        changed['current']['nextAction'] = 'A newly authorized next action'
        self.write_task(changed)
        before = sorted(path.relative_to(self.root) for path in self.root.rglob('*'))
        stale = subprocess.run(command + ['--check'], capture_output=True, text=True)
        self.assertNotEqual(stale.returncode, 0)
        self.assertEqual((now.read_bytes(), now.stat().st_mtime_ns), (content, modified))
        self.assertEqual(before, sorted(path.relative_to(self.root) for path in self.root.rglob('*')))
        self.assertEqual(subprocess.run(command, capture_output=True).returncode, 0)
        self.assertEqual(subprocess.run(command + ['--check'], capture_output=True).returncode, 0)

    def test_empty_frontier_now_ends_in_exactly_one_newline(self):
        path = self.root / 'work/frontier.json'
        data = json.loads(path.read_text())
        data['product'] = []
        path.write_text(json.dumps(data))
        (self.root / 'work/tasks/RUN-001.json').unlink()
        state = self.state()
        content = work.now_markdown(state, state['repositories'][0])
        self.assertTrue(content.endswith('## Parallel\n'))
        self.assertFalse(content.endswith('\n\n'))
        self.assertEqual(subprocess.run([sys.executable, str(TOOL), '--root', str(self.root),
                                        'build'], capture_output=True).returncode, 0)
        self.assertEqual((self.root / 'work/NOW.md').read_bytes(), content.encode('utf-8'))

    def test_payload_whitelist_and_rich_blockers(self):
        data = task()
        data['history'] = ['PRIVATE-HISTORY-MARKER' * 10000]
        data['checkpoint'] = {'arbitrary': 'PRIVATE-CHECKPOINT-MARKER'}
        data['current']['blockers'] = [{'id': 'B1', 'area': 'consumer', 'observed': 'Unavailable',
            'sources': [{'path': 'evidence.log'}], 'exit': 'Consumer succeeds', 'disposition': 'open'}]
        self.write_task(data)
        state = self.state()
        payload = work.overview(state)
        encoded = json.dumps(payload)
        self.assertNotIn('PRIVATE-', encoded)
        self.assertNotIn('evidence.log', encoded)
        self.assertNotIn('Consumer succeeds', encoded)
        self.assertFalse(payload['tasks'][0]['ready'])
        detail = work.task_detail(state, 'sample/one', 'RUN-001')
        self.assertEqual(detail['current']['blockers'][0]['exit'], 'Consumer succeeds')
        self.assertNotIn('history', detail)

    def test_discovery_ignores_hidden_symlink_and_non_git(self):
        self.repository('.hidden', 'sample/hidden')
        plain = self.workspace / 'plain/work'
        plain.mkdir(parents=True)
        (plain / 'frontier.json').write_text('{}')
        (self.workspace / 'linked').symlink_to(self.root, target_is_directory=True)
        self.assertEqual(work.discover(self.workspace), [self.root])
        retired = self.repository('.retired', 'sample/old', 'retired')
        state = work.snapshot(work.discover(self.workspace, [retired]))
        row = work.overview(state, repository='sample/old')['tasks'][0]
        self.assertEqual(row['lifecycle'], 'retired')
        self.assertFalse(row['ready'])

    def test_no_following_symlinked_input(self):
        path = self.root / 'work/tasks/RUN-001.json'
        saved = self.workspace / 'secret.json'
        path.rename(saved)
        path.symlink_to(saved)
        loaded = work.load_repository(self.root)
        self.assertTrue(any('symlinked' in e for e in loaded['errors']))
        self.assertEqual(loaded['tasks'], {})

    def start_server(self):
        server = work.make_server(self.workspace, port=0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        self.addCleanup(server.server_close)
        self.addCleanup(server.shutdown)
        return 'http://127.0.0.1:' + str(server.server_port)

    def get(self, url):
        with urlopen(url, timeout=5) as response:
            return json.load(response)

    def test_http_filter_detail_poll_live_edit_and_read_only(self):
        data = task()
        data['history'] = ['HISTORY-SHOULD-NOT-LEAK']
        self.write_task(data)
        base = self.start_server()
        before_files = sorted(p.relative_to(self.workspace) for p in self.workspace.rglob('*'))
        initial = self.get(base + '/api/overview?repository=sample%2Fone&status=planned&search=useful')
        self.assertEqual(initial['total'], 1)
        self.assertNotIn('HISTORY-SHOULD-NOT-LEAK', json.dumps(initial))
        detail = self.get(base + '/api/task?repository=sample%2Fone&id=RUN-001')
        self.assertEqual(detail['acceptance'], data['acceptance'])
        self.assertNotIn('history', detail)
        data['status'] = 'in-progress'
        data['current']['summary'] = '<img src=x onerror=alert(1)>'
        self.write_task(data)
        changed = self.get(base + '/api/overview?status=in-progress')
        self.assertNotEqual(initial['identity'], changed['identity'])
        self.assertEqual(changed['total'], 1)
        self.assertEqual(self.get(base + '/api/overview?status=planned')['total'], 0)
        self.assertEqual(before_files, sorted(p.relative_to(self.workspace) for p in self.workspace.rglob('*')))
        with urlopen(base, timeout=5) as response:
            html = response.read().decode()
            self.assertIn('textContent', html)
            self.assertNotIn('innerHTML', html)
            self.assertIn('setInterval', html)
            self.assertIn('frame-ancestors', response.headers['Content-Security-Policy'])
        for path in ('/../../secret.json', '/work/tasks/RUN-001.json', '/api/task?repository=sample%2Fone&id=..%2Fsecret'):
            with self.assertRaises(HTTPError) as error:
                self.get(base + path)
            self.assertIn(error.exception.code, (400, 404))
            error.exception.close()
        for method in ('POST', 'PUT', 'PATCH', 'DELETE'):
            with self.assertRaises(HTTPError) as error:
                urlopen(Request(base + '/api/overview', data=b'{}', method=method), timeout=5)
            self.assertEqual(error.exception.code, 405)
            error.exception.close()
        with self.assertRaises(HTTPError) as error:
            urlopen(Request(base, headers={'Host': 'foreign.example'}), timeout=5)
        self.assertEqual(error.exception.code, 403)
        error.exception.close()

    def test_http_malformed_frontier_remains_a_diagnostic_view(self):
        path = self.root / 'work/frontier.json'
        data = json.loads(path.read_text())
        data['repository'] = ['wrong type']
        data['product'] = 123
        path.write_text(json.dumps(data))
        base = self.start_server()
        payload = self.get(base + '/api/overview?scope=all')
        self.assertTrue(payload['repositories'][0]['errors'])
        self.assertFalse(payload['tasks'][0]['ready'])

    @unittest.skipUnless(os.environ.get('PROJECT_WORK_BROWSER_MODULE'), 'optional own-process browser runtime not selected')
    def test_own_headless_ui_groups_issues_and_filter_loading(self):
        one = task(status='in-progress', depends=['absent/repository#RUN-001'])
        one['current']['blockers'] = ['Current obstruction']
        self.write_task(one)
        self.write_task(task('RUN-002', 'planned', ['absent/repository#RUN-002']))
        self.write_task(task('RUN-003', 'done'))
        self.write_task(task('RUN-004', 'cancelled'))
        self.write_task(task('LATER-001'))
        path = self.root / 'work/frontier.json'
        frontier = json.loads(path.read_text())
        frontier['product'] = ['RUN-001', 'RUN-002', 'RUN-003', 'RUN-004']
        path.write_text(json.dumps(frontier))
        two = self.repository('two', 'sample/two')
        self.write_task(task(status='in-progress'), two)
        two_frontier = two / 'work/frontier.json'
        invalid = json.loads(two_frontier.read_text())
        invalid['product'].append('MISSING-001')
        two_frontier.write_text(json.dumps(invalid))
        result = subprocess.run(['node', str(TOOL.parent / 'tests/project_work_ui_smoke.cjs'),
                                 self.start_server()], capture_output=True, text=True, timeout=45)
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_http_pagination_is_bounded(self):
        for number in range(2, 110):
            self.write_task(task('RUN-' + str(number).zfill(3)))
        base = self.start_server()
        page = self.get(base + '/api/overview?scope=all&limit=10000')
        self.assertEqual(page['total'], 109)
        self.assertEqual(len(page['tasks']), 100)
        self.assertEqual(len(self.get(base + '/api/overview?scope=all&offset=100')['tasks']), 9)


if __name__ == '__main__':
    unittest.main()
