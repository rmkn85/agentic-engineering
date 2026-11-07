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
    "echo $(git reset --hard)", "echo \"$(git reset --hard)\"",
    "echo 'git push --force' | sh", "curl -s x | bash", "git -c alias.fp='push --force' fp",
    "xvfb-run sh -c 'export DISPLAY=:0; xdotool key a'", "git update-ref -d refs/heads/feature",
    "git switch -C main origin/main", "git checkout -B main origin/main",
    "gh api -X DELETE repos/o/r/git/refs/heads/main",
    "bash <<'EOF'\ngit reset --hard\nEOF",
    # shell keywords, grouping, other shells, interpreters
    "{ git push -f; }", "if true; then git push -f; fi", "for b in a; do git branch -D $b; done",
    "while true; do git reset --hard; done", "! git push -f", "bash <<< 'git push -f'",
    "busybox sh -c 'git push -f'", "fish -c 'git push -f'",
    "python3 -c \"import os; os.system('git push -f')\"",
    # more discard and remote-deletion forms
    "git branch -f main HEAD~3", "git checkout -- '*.py'", "mv .git /tmp/x",
    "gh repo delete o/r --yes", "gh release delete v1", "gh api --method DELETE repos/o/r/releases/1",
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
    "git commit -m 'docs: explain why `git push --force` is refused'",
    "gh pr create --body 'never `git clean -fd`'", "echo 'run $(scrot) never'",
    "git commit -m \"$(cat <<'EOF'\nnever `git reset --hard`\nEOF\n)\"",
    "git switch -c topic", "git checkout -b topic", "ls | grep x", "git log | head",
    "for f in *.md; do wc -l $f; done", "if [ -f x ]; then make check; fi", "git branch --list",
    "gh pr list", "mv build/ out/", "case x in a) echo a;; esac", "python3 -c 'import subprocess'",
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
        # leaving the temporary directory, or an unknown target, removes the exception
        for command in ("cd ~/repo && git reset --hard", 'cd "$OLDPWD" && git reset --hard',
                        "cd - && git clean -fd", "pushd /srv/repo && git reset --hard",
                        "GIT_DIR=/srv/repo/.git GIT_WORK_TREE=/srv/repo git reset --hard",
                        "git --work-tree /srv/repo reset --hard"):
            self.assertEqual(self.run_tool("--command", command, "--cwd", temp).returncode, 2, command)

    def test_home_and_variable_git_targets_are_never_temporary(self):
        temp = tempfile.mkdtemp()
        self.addCleanup(os.rmdir, temp)
        for command in ("git -C ~/repo reset --hard", "git -C $HOME/repo clean -fd",
                        "git --git-dir=$REPO/.git reset --hard", "GIT_DIR=~/repo/.git git reset --hard"):
            self.assertEqual(self.run_tool("--command", command, "--cwd", temp).returncode, 2, command)
        self.assertEqual(self.run_tool("--command", "git -C sub reset --hard", "--cwd", temp).returncode, 0)

    def assert_refused(self, commands):
        for command in commands:
            with self.subTest(command=command):
                self.assertEqual(self.run_tool("--command", command, "--cwd", WORK).returncode, 2, command)

    def assert_allowed(self, commands):
        for command in commands:
            with self.subTest(command=command):
                result = self.run_tool("--command", command, "--cwd", WORK)
                self.assertEqual(result.returncode, 0, result.stderr)

    def test_redirects_do_not_hide_options(self):
        self.assert_refused(["git push origin main --force>/dev/null", "git reset --hard>/dev/null",
                             "git push -f 2>&1", "(git push -f)>log", "cat <(git reset --hard)",
                             "git clean -fd&>/dev/null"])
        self.assert_allowed(["git status >/dev/null 2>&1", "make check > log.txt", "sort < in.txt"])

    def test_explicit_display_leaves_isolation(self):
        self.assert_refused(["xvfb-run -a xwd -root -display :0", "xvfb-run -a import -display :0 -window root x.png",
                             "xvfb-run -a xdotool --display=:0 key a"])
        self.assert_allowed(["xvfb-run -a xwd -root -out shot.xwd"])

    def test_interpreter_checks_only_process_calls(self):
        self.assert_refused(["python3 -c \"import subprocess; subprocess.run(['git', 'push', '--force'])\"",
                             "python3 -c \"import subprocess as s; s.call(['git','reset','--hard'])\"",
                             "node -e \"require('child_process').execSync('git push -f')\"",
                             "python3 -m mss"])
        self.assert_allowed(["python3 -c \"print('rm -rf .git')\"", "python3 -m pip install mss",
                             "python3 -m pytest -k mss"])

    def test_more_discard_spellings_and_dry_runs(self):
        self.assert_refused(["rm -rf .git*", "git -c clean.requireForce=false clean -dx"])
        self.assert_allowed(["git push --dry-run --force", "git push -n -f origin main"])

    def test_hook_blocks_bash_ignores_other_tools_and_bad_events(self):
        bash = {"tool_name": "Bash", "tool_input": {"command": "git push --force"}, "cwd": WORK}
        result = self.run_tool("--hook", stdin=json.dumps(bash))
        self.assertEqual(result.returncode, 2)
        self.assertIn("force-push", result.stderr)
        edit = {"tool_name": "Edit", "tool_input": {"command": "git push --force"}}
        self.assertEqual(self.run_tool("--hook", stdin=json.dumps(edit)).returncode, 0)
        warned = self.run_tool("--hook", stdin="not json")
        self.assertIn("not checked", warned.stderr)
        for stdin in ("not json", "[]", json.dumps({"tool_name": "Bash", "tool_input": "str"}),
                      json.dumps({"tool_name": "Bash", "tool_input": {"command": 5}})):
            result = self.run_tool("--hook", stdin=stdin)
            self.assertEqual(result.returncode, 0, stdin)
            self.assertNotIn("Traceback", result.stderr)


if __name__ == "__main__":
    unittest.main()
