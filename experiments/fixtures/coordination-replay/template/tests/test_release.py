import tempfile
import unittest
from pathlib import Path

from release import publish


class ReleaseTests(unittest.TestCase):
    def test_initial_publish_reaches_consumer(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / "source.txt"
            source.write_text("first payload\n", encoding="utf-8")
            receipt = publish(source, Path(root) / "work", "v1")
            self.assertEqual(receipt["served_text"], "first payload\n")
            self.assertEqual(receipt["source_sha256"], receipt["served_sha256"])

    def test_new_version_reaches_consumer(self):
        with tempfile.TemporaryDirectory() as root:
            source = Path(root) / "source.txt"
            work = Path(root) / "work"
            source.write_text("first payload\n", encoding="utf-8")
            publish(source, work, "v1")
            source.write_text("second payload\n", encoding="utf-8")
            receipt = publish(source, work, "v2")
            self.assertEqual(receipt["served_text"], "second payload\n")


if __name__ == "__main__":
    unittest.main()
