"""Load drill definitions."""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path

from .paths import EXERCISES, WORKSPACE


@dataclass(frozen=True)
class Drill:
    number: int
    id: str
    title: str
    skill: str
    summary: str
    files: list = field(default_factory=list)
    hints: list = field(default_factory=list)

    @property
    def folder(self) -> Path:
        return EXERCISES / self.id

    @property
    def starter(self) -> Path:
        return self.folder / "starter"

    @property
    def solution(self) -> Path:
        return self.folder / "solution"

    @property
    def work(self) -> Path:
        return WORKSPACE / self.id


def all_drills() -> list:
    out = []
    for meta in sorted(EXERCISES.glob("*/meta.json")):
        d = json.loads(meta.read_text(encoding="utf-8"))
        out.append(Drill(**{k: d[k] for k in ("number", "id", "title", "skill", "summary", "files", "hints")}))
    return sorted(out, key=lambda d: d.number)


def find(ref: str) -> Drill:
    ref = str(ref).strip().lower()
    for d in all_drills():
        if ref in (str(d.number), f"{d.number:02d}", d.id) or d.id.startswith(ref):
            return d
    raise SystemExit(f"No drill called '{ref}'. Run: python3 -m drills list")
