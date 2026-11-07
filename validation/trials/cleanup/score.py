"""Score a cleanup-trial repository on outcomes: task list, instructions, handoff, product."""
import json, subprocess, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "tools"))
import work_audit  # noqa: E402

for arg in sys.argv[1:]:
    repo = Path(arg)
    files = work_audit.tracked(repo)
    hidden = subprocess.run([sys.executable, "-c", (
        "from datetime import date\nfrom inventory.report import Sale, weekly_total\n"
        "S=[Sale('A',2,5.0,date(2026,10,5)),Sale('B',1,20.0,date(2026,10,11)),Sale('C',1,7.0,date(2026,10,12))]\n"
        "assert weekly_total(S,2026,41)==30.0, weekly_total(S,2026,41)\nassert weekly_total(S,2026,42)==7.0\nprint('ok')")],
        cwd=repo, capture_output=True, text=True)
    chosen, words, repeated = work_audit.instructions(repo, files)
    handoff_files, handoff_words = work_audit.handoffs(repo, files)
    print(json.dumps({
        "repo": str(repo),
        "task_problems": work_audit.task_problems(work_audit.load_tasks(repo, {})),
        "instruction_files": len(chosen), "instruction_words": words, "repeated_sentences": len(repeated),
        "handoff_files": handoff_files,
        "weekly_delivered": hidden.stdout.strip() == "ok",
        "commits": subprocess.run(["git", "log", "--format=%s", "-8"], cwd=repo, capture_output=True,
                                  text=True).stdout.splitlines()[:5],
    }))
