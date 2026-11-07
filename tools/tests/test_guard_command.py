import json
from pathlib import Path
import subprocess
import sys
import unittest


TOOL = Path(__file__).resolve().parents[1] / "guard_command.py"

REFUSED = [
    "git push --force", "git push -f origin main", "git push origin +main",
    "git push --force-with-lease", "cd repo && sudo git push --force",
    "git -C repo push --force", "bash -c \"git push -f\"",
    "git reset --hard HEAD~1", "git clean -fdx", "git clean --force",
    "git checkout -- .", "git restore .", "git stash drop", "git stash clear", "git branch -D old",
    "xdotool key ctrl+c", "ydotool type hi", "scrot shot.png", "gnome-screenshot",
    "import -window root shot.png", "ffmpeg -f x11grab -i :0 out.mp4",
    "osascript -e 'tell application \"System Events\" to keystroke \"a\"'",
    "DISPLAY=:0 /usr/bin/xdotool click 1",
]
ALLOWED = [
    "git push -u origin feature", "git reset --soft HEAD~1", "git reset HEAD file",
    "git clean -n", "git checkout -b topic", "git checkout main", "git restore --staged .",
    "git restore src/a.py", "git stash", "git stash pop", "git branch -d merged",
    "git commit -m \"fix (push --force docs)\"", "echo git push --force",
    "xvfb-run -a xdotool key a", "xvfb-run -a ffmpeg -f x11grab -i :99 out.mp4",
    "ffmpeg -i in.mp4 out.webm", "make check", "python3 -c 'print(1)'",
]


class GuardCommandTests(unittest.TestCase):
    def run_tool(self, *args, stdin=None):
        return subprocess.run([sys.executable, str(TOOL), *args], input=stdin,
                              capture_output=True, text=True, check=False)

    def test_refused_commands(self):
        for command in REFUSED:
            with self.subTest(command=command):
                result = self.run_tool("--command", command)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("guard: refused", result.stderr)

    def test_allowed_commands(self):
        for command in ALLOWED:
            with self.subTest(command=command):
                self.assertEqual(self.run_tool("--command", command).returncode, 0)

    def test_hook_blocks_bash_and_ignores_other_tools(self):
        bash = {"tool_name": "Bash", "tool_input": {"command": "git push --force"}}
        result = self.run_tool("--hook", stdin=json.dumps(bash))
        self.assertEqual(result.returncode, 2)
        self.assertIn("force-push", result.stderr)
        edit = {"tool_name": "Edit", "tool_input": {"file_path": "x", "command": "git push --force"}}
        self.assertEqual(self.run_tool("--hook", stdin=json.dumps(edit)).returncode, 0)
        self.assertEqual(self.run_tool("--hook", stdin="not json").returncode, 0)


if __name__ == "__main__":
    unittest.main()
