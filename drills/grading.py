"""Run a grader with a time limit and read its result."""
from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

from .paths import REPO

TIME_LIMIT = int(os.environ.get("DRILLS_TIME_LIMIT", "60"))


def run_grader(drill_id: str, folder: Path) -> list:
    try:
        proc = subprocess.run([sys.executable, "-B", "-m", "drills.grade_runner", drill_id, str(folder)],
                              cwd=REPO, capture_output=True, text=True, timeout=TIME_LIMIT)
    except subprocess.TimeoutExpired:
        return [{"name": "finishes in time", "ok": False,
                 "detail": f"still running after {TIME_LIMIT} seconds. Is there a loop that never ends?"}]
    out = proc.stdout
    if "@@CHECKS@@" not in out:
        tail = (proc.stderr.strip().splitlines() or ["no output"])[-1]
        return [{"name": "grader ran", "ok": False, "detail": tail[:200]}]
    return json.loads(out.rsplit("@@CHECKS@@", 1)[1])
