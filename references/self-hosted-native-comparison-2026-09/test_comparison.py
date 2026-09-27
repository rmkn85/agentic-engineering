import importlib.util
import unittest
from pathlib import Path
spec=importlib.util.spec_from_file_location('comparison',Path(__file__).with_name('compare.py'))
comparison=importlib.util.module_from_spec(spec);spec.loader.exec_module(comparison)

class ComparisonTests(unittest.TestCase):
    def test_fixture_is_exact_original(self):
        comparison.verify_fixture()

    def test_startup_library_error_is_retained_without_path(self):
        result=comparison.safe_error('/private/user/tool: error while loading shared libraries: libExample.so: cannot open shared object file')
        self.assertIn('libExample.so', result)
        self.assertNotIn('/private',result)

    def test_no_unrelated_info_in_diagnostics(self):
        result=comparison.safe_error('Adapter secret-device-name\nHome /private/home\nERROR: cannot load /private/work/file')
        self.assertEqual(len(result),1)
        self.assertNotIn('secret-device-name',result[0])
        self.assertNotIn('/private',result[0])

    def test_missing_log_error_is_not_fabricated(self):
        self.assertEqual(comparison.safe_error('Engine started\n'),[])

if __name__=='__main__':unittest.main()
