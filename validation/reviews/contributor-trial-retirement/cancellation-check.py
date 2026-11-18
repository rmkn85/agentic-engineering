"""Bounded cancellation reproduction using a fake child; no processes launched."""
import importlib.util
import json
from pathlib import Path
import tempfile
from unittest import mock

root = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location("fresh", root / "tools/check-fresh.py")
fresh = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fresh)
with tempfile.TemporaryDirectory() as folder:
    output = Path(folder)
    child = mock.Mock()
    child.wait.side_effect = [KeyboardInterrupt(), 0]
    with mock.patch.object(fresh, "git", side_effect=[folder, "candidate", "tree", "", "parent"]), \
         mock.patch.object(fresh.subprocess, "Popen", return_value=child), \
         mock.patch.object(fresh.os, "killpg") as killpg:
        interrupted = False
        receipt = {}
        try:
            receipt = fresh.exercise(output, ["trusted-check"], output, 1)
        except KeyboardInterrupt:
            interrupted = True
    result = {"interrupt_propagated": interrupted,
              "execution_removed": not (output / "execution").exists(),
              "child_group_stop_called": killpg.called,
              "child_stop_called": child.kill.called or child.terminate.called,
              "wait_calls": child.wait.call_count,
              "receipt_written": (output / "receipt.json").exists(),
              "reason": receipt.get("reason"),
              "method": "mocked child and Git identity; no real child process"}
    print(json.dumps(result, sort_keys=True))
    assert not interrupted and result["execution_removed"]
    assert result["reason"] == "trial_cancelled"
    assert result["child_group_stop_called"] or result["child_stop_called"]
    assert result["wait_calls"] == 2
