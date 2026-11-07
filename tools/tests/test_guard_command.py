import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


TOOL = Path(__file__).resolve().parents[1] / "guard_command.py"
WORK = "/srv/work/repo"  # a fixed non-temporary location; the guard never touches it

REFUSED = [
    # force-push and remote deletion
    "git push --force", "git push -f origin main", "git push -uf origin x", "git push origin +main",
    "git push --force-with-lease", "cd repo && sudo git push --force", "git -C repo push --force",
    "git push origin --delete feature", "git push origin :feature",
    # discard
    "git reset --hard HEAD~1", "git clean -fdx", "git clean --force", "git checkout -- .",
    "git checkout -f main", "git checkout HEAD -- src/", "git switch --discard-changes main",
    "git restore .", "git restore src/", "git stash drop", "git stash clear", "git branch -D old",
    "git branch --delete --force x", "git branch -d -f x", "git worktree remove --force ../wt",
    "rm -rf .git",
    # wrappers and indirection
    "bash -c \"git push -f\"", "sh -ec \"git reset --hard\"", "bash -lc 'git clean -fd'",
    "echo x | xargs git reset --hard", "find . -name x -exec git reset --hard \\;", "eval git push --force",
    "sudo -u root xdotool key a", "timeout -s KILL 5 xdotool key a", "env -i git push -f",
    "echo $(git reset --hard)",
    # desktop
    "xdotool key ctrl+c", "ydotool type hi", "scrot shot.png", "gnome-screenshot",
    "import -window root shot.png", "ffmpeg -f x11grab -i :0 out.mp4",
    "gst-launch-1.0 ximagesrc ! fakesink", "python3 -c 'import pyautogui; pyautogui.click()'",
    "osascript -e 'tell application \"System Events\" to keystroke \"a\"'",
    "DISPLAY=:0 /usr/bin/xdotool click 1", "xvfb-run -a bash -c \"DISPLAY=:0 xdotool key a\"",
    "gdbus call --session --dest org.gnome.Shell.Screenshot --method org.gnome.Shell.Screenshot.Screenshot",
]
ALLOWED = [
    "git push -u origin feature", "git push origin main", "git reset --soft HEAD~1", "git reset HEAD file",
    "git reset --keep HEAD~1", "git clean -n", "git checkout -b topic", "git checkout main",
    "git restore --staged .", "git restore src/a.py", "git checkout HEAD -- src/a.py", "git stash",
    "git stash pop", "git branch -d merged", "git worktree remove ../wt",
    # quoted text is data
    "git commit -m \"fix (push --force docs)\"", "git commit -m \"explain; git reset --hard is refused\"",
    "git commit -m \"docs: never run (git push --force) on main\"",
    "gh pr create --body \"Guard refuses; git branch -D x\"", "echo git push --force",
    "git commit -m \"first line\nsecond line; git clean -fd\"",
    "cat > notes.md <<'EOF'\ngit push --force is refused\nxdotool key a\nEOF",
    # isolated display and ordinary work
    "xvfb-run -a xdotool key a", "xvfb-run -a ffmpeg -f x11grab -i :99 out.mp4",
    "xvfb-run -s '-screen 0 1280x720x24' python3 -c 'import pyautogui'",
    "ffmpeg -i in.mp4 out.webm", "make check", "python3 -c 'print(1)'", "rm -rf build/",
]


class GuardCommandTests(unittest.TestCase):
    def run_tool(self, *args, stdin=None):
        return subprocess.run([sys.executable, str(TOOL), *args], input=stdin,
                              capture_output=True, text=True, check=False)

    def test_refused_commands(self):
        for command in REFUSED:
            with self.subTest(command=command):
                result = self.run_tool("--command", command, "--cwd", WORK)
                self.assertEqual(result.returncode, 2, result.stderr)
                self.assertIn("guard: refused", result.stderr)

    def test_allowed_commands(self):
        for command in ALLOWED:
            with self.subTest(command=command):
                result = self.run_tool("--command", command, "--cwd", WORK)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_disposable_clones_in_temp_may_discard_but_never_force_push(self):
        temp = tempfile.mkdtemp()
        self.addCleanup(os.rmdir, temp)
        self.assertEqual(self.run_tool("--command", f"cd {temp} && git reset --hard origin/main").returncode, 0)
        self.assertEqual(self.run_tool("--command", "git clean -fdx", "--cwd", temp).returncode, 0)
        self.assertEqual(self.run_tool("--command", f"git -C {temp} reset --hard").returncode, 0)
        self.assertEqual(self.run_tool("--command", "git push --force", "--cwd", temp).returncode, 2)

    def test_hook_blocks_bash_ignores_other_tools_and_bad_events(self):
        bash = {"tool_name": "Bash", "tool_input": {"command": "git push --force"}, "cwd": WORK}
        result = self.run_tool("--hook", stdin=json.dumps(bash))
        self.assertEqual(result.returncode, 2)
        self.assertIn("force-push", result.stderr)
        edit = {"tool_name": "Edit", "tool_input": {"command": "git push --force"}}
        self.assertEqual(self.run_tool("--hook", stdin=json.dumps(edit)).returncode, 0)
        for stdin in ("not json", "[]", json.dumps({"tool_name": "Bash", "tool_input": "str"}),
                      json.dumps({"tool_name": "Bash", "tool_input": {"command": 5}})):
            result = self.run_tool("--hook", stdin=stdin)
            self.assertEqual(result.returncode, 0, stdin)
            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
