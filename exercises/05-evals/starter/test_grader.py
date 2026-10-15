"""Runs the labeled examples in cases.json. Run: python3 test_grader.py"""
import json
from pathlib import Path

from grader import grade

CASES = json.loads((Path(__file__).parent / "cases.json").read_text(encoding="utf-8"))

if __name__ == "__main__":
    passed = 0
    for c in CASES:
        got = grade(c["question"], c["reference"], c["answer"])
        ok = got is c["correct"]
        passed += ok
        print("PASS" if ok else "FAIL", f"want {c['correct']}: {c['answer']}")
    print(f"{passed} of {len(CASES)} visible tests passed")
