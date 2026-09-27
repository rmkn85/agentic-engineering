"""Opt-in default-driver policy regression tests; native runs remain separate."""
import importlib.util
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
spec = importlib.util.spec_from_file_location('configured_native', Path(__file__).with_name('run.py'))
probe = importlib.util.module_from_spec(spec)
spec.loader.exec_module(probe)

class ConfiguredDriverTests(unittest.TestCase):
    def test_empty_inherited_configuration_adds_no_driver_choice(self):
        self.assertEqual(probe.driver_environment({}, True), {})

    def test_existing_driver_choices_are_preserved_exactly(self):
        original = {key: 'existing-' + key for key in probe.DRIVER_KEYS}
        self.assertEqual(probe.driver_environment(original, True), original)

    def test_credentials_and_interactive_display_never_enter_child_environment(self):
        original = {'GITHUB_TOKEN':'secret','GH_TOKEN':'secret','DISPLAY':':0',
                    'WAYLAND_DISPLAY':'desktop','GALLIUM_DRIVER':'configured'}
        self.assertEqual(probe.driver_environment(original, True), {'GALLIUM_DRIVER':'configured'})

    def test_previous_software_case_remains_explicit_and_unchanged(self):
        self.assertEqual(probe.driver_environment({'GALLIUM_DRIVER':'other'}), {
            'LIBGL_ALWAYS_SOFTWARE':'1','GALLIUM_DRIVER':'llvmpipe',
            '__GLX_VENDOR_LIBRARY_NAME':'mesa','LP_NUM_THREADS':'1'})

    def test_configured_launch_keeps_temp_state_owned_and_does_not_force_driver(self):
        with tempfile.TemporaryDirectory() as temp, patch.dict(os.environ, {'PATH':'/usr/bin:/bin'}, clear=True):
            with patch.object(probe.subprocess, 'Popen') as popen:
                worker = probe.launch(Path('/fixture/godot'), Path(temp), 0, True, True, 0, [0], True)
                worker['log'].close()
                env = popen.call_args.kwargs['env']
                self.assertFalse(set(probe.DRIVER_KEYS) & set(env))
                for key in ('TMPDIR','HOME','XDG_RUNTIME_DIR','PROBE_OUTPUT'):
                    self.assertTrue(Path(env[key]).is_relative_to(Path(temp)))
                self.assertNotIn('DISPLAY', env)
                self.assertNotIn('--headless', popen.call_args.args[0])

    def test_headless_configured_launch_stays_non_rendering(self):
        with tempfile.TemporaryDirectory() as temp, patch.object(probe.subprocess,'Popen') as popen:
            worker=probe.launch(Path('/fixture/godot'), Path(temp), 0, False, True, 0, [0], True)
            worker['log'].close()
            self.assertIn('--headless',popen.call_args.args[0])
            self.assertNotIn('xvfb-run',popen.call_args.args[0])

if __name__ == '__main__':
    unittest.main()
