import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

TOOL = Path(__file__).resolve().parents[1] / "check_workflow_pins.py"


class WorkflowPinTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def write_workflow(self, repo: str, filename: str, content: str) -> None:
        path = self.root / repo / ".github" / "workflows" / filename
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def run_tool(self, *args: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            [sys.executable, str(TOOL), *args],
            capture_output=True,
            text=True,
            check=False,
        )

    def test_clean_shared_ref(self):
        wf = (
            "jobs:\n"
            "  verify:\n"
            "    uses: org/shared/.github/workflows/check.yml@main\n"
            "    with:\n"
            "      tooling_revision: main\n"
        )
        self.write_workflow("repo-a", "ci.yml", wf)
        self.write_workflow("repo-b", "ci.yml", wf)
        result = self.run_tool("--discover", "--strict", str(self.root))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("clean (2 repos, 2 reusable workflow calls)", result.stdout)

    def test_workflow_ref_drift(self):
        self.write_workflow(
            "repo-a",
            "ci.yml",
            "jobs:\n  verify:\n    uses: org/shared/.github/workflows/check.yml@main\n",
        )
        self.write_workflow(
            "repo-b",
            "ci.yml",
            "jobs:\n  verify:\n    uses: org/shared/.github/workflows/check.yml@aaaa111\n",
        )
        result = self.run_tool("--discover", "--strict", str(self.root))
        self.assertEqual(result.returncode, 1)
        self.assertIn("[workflow-ref-drift]", result.stdout)
        self.assertIn("repo-a:ci.yml", result.stdout.replace(".github/workflows/", ""))

    def test_input_pin_drift(self):
        self.write_workflow(
            "repo-a",
            "ci.yml",
            "jobs:\n  verify:\n    uses: org/shared/.github/workflows/check.yml@main\n"
            "    with:\n      tooling_revision: aaaa111111111111111111111111111111111111\n",
        )
        self.write_workflow(
            "repo-b",
            "ci.yml",
            "jobs:\n  verify:\n    uses: org/shared/.github/workflows/check.yml@main\n"
            "    with:\n      tooling_revision: bbbb222222222222222222222222222222222222\n",
        )
        result = self.run_tool("--discover", "--strict", str(self.root))
        self.assertEqual(result.returncode, 1)
        self.assertIn("[input-pin-drift]", result.stdout)
        self.assertIn("tooling_revision", result.stdout)

    def test_sha_ref_input_mismatch(self):
        self.write_workflow(
            "repo-a",
            "ci.yml",
            "jobs:\n"
            "  verify:\n"
            "    uses: org/shared/.github/workflows/check.yml@1111111111111111111111111111111111111111\n"
            "    with:\n"
            "      tooling_revision: '2222222222222222222222222222222222222222'\n",
        )
        result = self.run_tool("--discover", "--strict", str(self.root))
        self.assertEqual(result.returncode, 1)
        self.assertIn("[ref-input-mismatch]", result.stdout)

    def test_expected_ref_and_json_output(self):
        self.write_workflow(
            "repo-a",
            "ci.yaml",
            "jobs:\n"
            "  verify:\n"
            "    uses: org/shared/.github/workflows/check.yml@v1.0.0\n",
        )
        result = self.run_tool(
            "--discover",
            "--expected-ref",
            "org/shared/.github/workflows/check.yml=main",
            "--json",
            "--strict",
            str(self.root),
        )
        self.assertEqual(result.returncode, 1)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["repos_scanned"], ["repo-a"])
        self.assertEqual(len(payload["references"]), 1)
        self.assertEqual(payload["findings"][0]["kind"], "expected-ref-mismatch")

    def test_ignores_comments_actions_and_hidden_dirs(self):
        self.write_workflow(
            "repo-a",
            "ci.yml",
            "# uses: org/shared/.github/workflows/check.yml@old\n"
            "jobs:\n"
            "  unit:\n"
            "    steps:\n"
            "      - uses: actions/checkout@v4\n"
            "  verify:\n"
            "    uses: org/shared/.github/workflows/check.yml@main # shared ref\n"
            "    with:\n"
            "      tooling_revision: main\n"
            "    secrets: inherit\n",
        )
        self.write_workflow(
            ".hidden-repo",
            "ci.yml",
            "jobs:\n  bad:\n    uses: org/shared/.github/workflows/check.yml@stale\n",
        )
        self.write_workflow(
            "node_modules/pkg",
            "ci.yml",
            "jobs:\n  bad:\n    uses: org/shared/.github/workflows/check.yml@stale\n",
        )
        result = self.run_tool("--discover", "--strict", "--match-ref", str(self.root))
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertIn("clean (1 repos, 1 reusable workflow calls)", result.stdout)

    def test_match_ref_flags_non_matching_branch_input(self):
        self.write_workflow(
            "repo-a",
            "ci.yml",
            "jobs:\n"
            "  verify:\n"
            "    uses: org/shared/.github/workflows/check.yml@main\n"
            "    with:\n"
            "      tooling_revision: v1.0.0\n",
        )
        result = self.run_tool("--discover", "--match-ref", "--strict", str(self.root))
        self.assertEqual(result.returncode, 1)
        self.assertIn("[ref-input-mismatch]", result.stdout)


if __name__ == "__main__":
    unittest.main()
