"""Offline coordinator regression tests; not substitutes for native Godot runs."""
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
spec = importlib.util.spec_from_file_location('parallel_probe', Path(__file__).with_name('run.py'))
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

class RunnerTests(unittest.TestCase):
    def test_required_different_parameters(self):
        self.assertEqual(len(set(probe.PARAMETERS)), 3)
        self.assertEqual([p[0] for p in probe.PARAMETERS], [4.9, 9.8, 19.6])

    def test_absent_or_partial_report_is_not_completion(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'result.json'
            self.assertIsNone(probe.read_json(path))
            path.write_text('{')
            self.assertIsNone(probe.read_json(path))
            path.write_text('{"completed":false}')
            self.assertEqual(probe.read_json(path), {'completed':False})

    def test_existing_output_is_not_overwritten(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)
            (p/'existing').write_text('keep')
            with self.assertRaises(FileExistsError):
                probe.group(Path('/missing-godot'), p, 1)
            self.assertEqual((p/'existing').read_text(),'keep')

    def test_stop_reaps_only_owned_process(self):
        proc=subprocess.Popen([sys.executable,'-S','-c','import time; time.sleep(20)'],start_new_session=True)
        probe.stop(proc)
        self.assertIsNotNone(proc.poll())
        # Already terminated children are also safe to reap.
        probe.stop(proc)

    def test_headless_and_real_render_launches_are_separate(self):
        with tempfile.TemporaryDirectory() as tmp:
            for i,rendered in enumerate([False,True]):
                with patch.object(probe.subprocess,'Popen') as popen:
                    parent=Path(tmp)/str(i);parent.mkdir()
                    worker=probe.launch(Path('/trusted/godot'),parent,0,rendered,True,0,[0])
                    worker['log'].close()
                    cmd=popen.call_args.args[0]
                    env=popen.call_args.kwargs['env']
                    self.assertEqual('--headless' in cmd,not rendered)
                    self.assertEqual('xvfb-run' in cmd,rendered)
                    self.assertEqual('--rendering-method' in cmd,rendered)
                    self.assertTrue(popen.call_args.kwargs['start_new_session'])
                    self.assertEqual(env['LP_NUM_THREADS'],'1')
                    self.assertNotIn('GITHUB_TOKEN',env)
                    self.assertNotIn('DISPLAY',env)
                    self.assertNotIn('WAYLAND_DISPLAY',env)

    def test_disjoint_projects_caches_user_data_and_outputs(self):
        with tempfile.TemporaryDirectory() as tmp:
            with patch.object(probe.subprocess,'Popen') as popen:
                workers=[]
                envs=[]
                for i in range(3):
                    workers.append(probe.launch(Path('/trusted/godot'),Path(tmp),i,False,True,0,[0,1,2]))
                    envs.append(popen.call_args.kwargs['env'])
                for w in workers:w['log'].close()
                for key in ['HOME','XDG_DATA_HOME','XDG_CONFIG_HOME','XDG_CACHE_HOME','XDG_RUNTIME_DIR','PROBE_OUTPUT','PROBE_CONFIG']:
                    self.assertEqual(len({e[key] for e in envs}),3,key)
                self.assertEqual(len({read['config']['gravity'] for read in workers}),3)

    def test_missing_engine_fails_and_keeps_log(self):
        with tempfile.TemporaryDirectory() as tmp:
            output=Path(tmp)/'run'
            with self.assertRaisesRegex(RuntimeError,'readiness'):
                probe.group(Path('/definitely-missing-godot'),output,1,timeout=2)
            self.assertTrue((output/'worker-1/engine.log').is_file())
            self.assertFalse((output/'summary.json').exists())

if __name__=='__main__':unittest.main()
