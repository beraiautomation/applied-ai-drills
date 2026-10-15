"""Runs one grader in its own process, so a stuck solution can't hang the CLI.

Usage: python -m drills.grade_runner <drill-id> <folder>
Prints a JSON list of checks.
"""
import importlib
import json
import sys
from pathlib import Path

from .exercises import find


def main() -> int:
    drill = find(sys.argv[1])
    folder = Path(sys.argv[2]).resolve()
    grader = importlib.import_module(f"drills.graders.g{drill.number:02d}")
    try:
        checks = [c.to_dict() for c in grader.grade(folder, drill.starter)]
    except Exception as exc:  # noqa: BLE001
        checks = [{"name": "grader ran", "ok": False, "detail": f"{type(exc).__name__}: {exc}"[:200]}]
    sys.stdout.write("\n@@CHECKS@@" + json.dumps(checks))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
