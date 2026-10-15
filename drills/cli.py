"""Command line: python3 -m drills <list|start|check|hint|reset|selftest>"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import shutil
import sys
from pathlib import Path

from . import __version__
from .exercises import all_drills, find
from .grading import run_grader
from .paths import WORKSPACE

if os.name == "nt":
    os.system("")
COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR") is None


def _c(code, text):
    return f"\033[{code}m{text}\033[0m" if COLOR else text


def bold(t): return _c("1", t)
def dim(t): return _c("2", t)
def green(t): return _c("32", t)
def red(t): return _c("31", t)
def purple(t): return _c("35", t)


PROGRESS = WORKSPACE / "progress.json"


def load_progress() -> dict:
    try:
        return json.loads(PROGRESS.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {}


def save_progress(data: dict) -> None:
    WORKSPACE.mkdir(exist_ok=True)
    PROGRESS.write_text(json.dumps(data, indent=2), encoding="utf-8")


def rel(path: Path) -> str:
    try:
        return str(path.relative_to(Path.cwd()))
    except ValueError:
        return str(path)


def cmd_list(_args) -> int:
    progress = load_progress()
    done = sum(1 for d in all_drills() if progress.get(d.id, {}).get("passed"))
    print()
    print(bold("Applied AI Drills") + dim(f"  ·  {done} of {len(all_drills())} passed"))
    print()
    for d in all_drills():
        p = progress.get(d.id, {})
        mark = green("✓") if p.get("passed") else (purple("•") if d.work.exists() else dim("○"))
        print(f" {mark} {bold(str(d.number))}  {bold(d.title):<44} {dim(d.skill)}")
        print(f"      {dim(d.summary)}")
    print()
    nxt = next((d for d in all_drills() if not progress.get(d.id, {}).get("passed")), None)
    if nxt:
        verb = "check" if nxt.work.exists() else "start"
        print("Next: " + bold(f"python3 -m drills {verb} {nxt.number}"))
    else:
        print(green("All drills passed. Nice work."))
    return 0


def cmd_start(args) -> int:
    d = find(args.drill)
    if d.work.exists():
        print(f"Drill {d.number} is already started in {bold(rel(d.work))}")
        print(dim("Use reset to start over."))
    else:
        WORKSPACE.mkdir(exist_ok=True)
        shutil.copytree(d.starter, d.work, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
        shutil.copy2(d.folder / "README.md", d.work / "README.md")
        print(green(f"Drill {d.number}: {d.title}"))
    print()
    print(f"  Read:   {bold(rel(d.work / 'README.md'))}")
    print(f"  Edit:   {bold(', '.join(rel(d.work / f) for f in d.files))}")
    print(f"  Check:  {bold(f'python3 -m drills check {d.number}')}")
    return 0


def cmd_check(args) -> int:
    d = find(args.drill)
    folder = Path(args.path).resolve() if args.path else d.work
    if not folder.exists():
        print(f"Drill {d.number} isn't started yet. Run: " + bold(f"python3 -m drills start {d.number}"))
        return 1
    print(dim(f"Checking drill {d.number}: {d.title} ..."))
    checks = run_grader(d.id, folder)
    passed = all(c["ok"] for c in checks)
    print()
    for c in checks:
        sign = green("✓") if c["ok"] else red("✗")
        print(f" {sign} {c['name']}" + (dim(f"  {c['detail']}") if c["detail"] else ""))
    print()
    if not args.path:
        progress = load_progress()
        entry = progress.setdefault(d.id, {})
        entry.update(passed=passed or entry.get("passed", False), last_check=dt.datetime.now().isoformat(timespec="seconds"))
        save_progress(progress)
    if passed:
        print(green(bold(f"Drill {d.number} passed.")))
        nxt = next((x for x in all_drills() if x.number > d.number), None)
        if nxt and not args.path:
            print("Next: " + bold(f"python3 -m drills start {nxt.number}") + dim(f"  ({nxt.title})"))
    else:
        left = sum(1 for c in checks if not c["ok"])
        print(f"{left} check{'s' if left != 1 else ''} to go. " + dim(f"Need a nudge? python3 -m drills hint {d.number}"))
    return 0 if passed else 1


def cmd_hint(args) -> int:
    d = find(args.drill)
    progress = load_progress()
    entry = progress.setdefault(d.id, {})
    shown = min(entry.get("hints", 0) + 1, len(d.hints))
    entry["hints"] = shown
    save_progress(progress)
    for i, h in enumerate(d.hints[:shown], 1):
        print(f"{purple(f'Hint {i}')}  {h}")
    if shown < len(d.hints):
        print(dim(f"\nRun it again for hint {shown + 1} of {len(d.hints)}."))
    return 0


def cmd_reset(args) -> int:
    d = find(args.drill)
    if d.work.exists() and not args.yes:
        print(f"This deletes your work in {rel(d.work)}. Run again with --yes to confirm.")
        return 1
    shutil.rmtree(d.work, ignore_errors=True)
    progress = load_progress()
    progress.pop(d.id, None)
    save_progress(progress)
    return cmd_start(args)


def cmd_selftest(_args) -> int:
    ok_all = True
    for d in all_drills():
        start_ok = not all(c["ok"] for c in run_grader(d.id, d.starter))
        sol = run_grader(d.id, d.solution)
        sol_ok = all(c["ok"] for c in sol)
        good = start_ok and sol_ok
        ok_all &= good
        print(f"{green('PASS') if good else red('FAIL')}  Drill {d.number}: starter fails = {start_ok}, solution passes = {sol_ok}")
        for c in sol:
            if not c["ok"]:
                print(red(f"      ✗ {c['name']}: {c['detail']}"))
    print()
    print(green("Every grader works.") if ok_all else red("Selftest failed."))
    return 0 if ok_all else 1


def main(argv=None) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        try:
            sys.stdout.reconfigure(encoding="utf-8")
        except Exception:  # noqa: BLE001
            pass
    p = argparse.ArgumentParser(prog="python3 -m drills", description="Fix broken AI systems. Code checks your work.")
    p.add_argument("--version", action="version", version=f"applied-ai-drills {__version__}")
    sub = p.add_subparsers(dest="command")
    sub.add_parser("list", help="show all drills and your progress").set_defaults(func=cmd_list)
    for name, fn, helptext in (("start", cmd_start, "copy a drill into workspace/ so you can work on it"),
                               ("check", cmd_check, "grade your work"),
                               ("hint", cmd_hint, "show the next hint"),
                               ("reset", cmd_reset, "start a drill over")):
        s = sub.add_parser(name, help=helptext)
        s.add_argument("drill", help="drill number or name, e.g. 2")
        if name == "check":
            s.add_argument("--path", help="check a different folder (for example, an agent's attempt)")
        if name == "reset":
            s.add_argument("--yes", action="store_true")
        s.set_defaults(func=fn)
    sub.add_parser("selftest", help="prove every grader works").set_defaults(func=cmd_selftest)
    args = p.parse_args(argv)
    if not getattr(args, "func", None):
        return cmd_list(args)
    try:
        return args.func(args)
    except KeyboardInterrupt:
        return 130
