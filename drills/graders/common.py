"""Shared helpers for graders."""
from __future__ import annotations

import hashlib
import importlib.util
import re
import subprocess
import sys
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class Check:
    name: str
    ok: bool
    detail: str = ""

    def to_dict(self):
        return asdict(self)


def load(folder: Path, module: str):
    """Import a module from the learner's folder, fresh every time."""
    sys.dont_write_bytecode = True
    if str(folder) not in sys.path:
        sys.path.insert(0, str(folder))
    spec = importlib.util.spec_from_file_location(f"learner_{module}_{uuid.uuid4().hex}", folder / f"{module}.py")
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def visible_tests(folder: Path, test_file: str, timeout: int = 30) -> Check:
    try:
        proc = subprocess.run([sys.executable, "-B", test_file], cwd=folder, capture_output=True,
                              text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        return Check("visible tests pass", False, f"took longer than {timeout} seconds")
    out = proc.stdout + proc.stderr
    m = re.search(r"(\d+) of (\d+) visible tests passed", out)
    ok = proc.returncode == 0 and bool(m) and m.group(1) == m.group(2)
    return Check("visible tests pass", ok, m.group(0) if m else (out.strip().splitlines() or ["no output"])[-1][:150])


def unchanged(folder: Path, original: Path, name: str) -> Check:
    f = folder / name
    if not f.exists():
        return Check(f"{name} not changed", False, "it was deleted")
    same = hashlib.sha256(f.read_bytes()).digest() == hashlib.sha256((original / name).read_bytes()).digest()
    return Check(f"{name} not changed", same, "" if same else "the test file was edited")


def score_cases(name: str, cases, fn) -> Check:
    """Run hidden cases. fn(case) returns None when OK or a short failure message."""
    fails = []
    for label, case in cases:
        try:
            problem = fn(case)
        except Exception as exc:  # noqa: BLE001
            problem = f"{type(exc).__name__}: {exc}"[:120]
        if problem:
            fails.append(f"{label}: {problem}")
    n = len(cases)
    detail = f"{n - len(fails)} of {n} passed" + (" · " + " · ".join(fails[:2]) if fails else "")
    return Check(name, not fails, detail)
