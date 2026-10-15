"""A few visible tests. Run: python3 test_rag.py"""
from pathlib import Path

from rag import chunk, retrieve

HANDBOOK = (Path(__file__).parent / "handbook.md").read_text(encoding="utf-8")

QUESTIONS = [
    ("How long do customers have to return an unused bike?", "Returns and refunds"),
    ("How much does a full service cost?", "Repairs and servicing"),
    ("What should I do with a swollen e-bike battery?", "Electric bike batteries"),
    ("How many days of paid holiday do full-time staff get?", "Holiday and time off"),
]


def top_sections(question):
    return [c["section"] for c in retrieve(chunk(HANDBOOK), question, k=3)]


if __name__ == "__main__":
    passed = 0
    for q, want in QUESTIONS:
        ok = any(want.lower() in s.lower() for s in top_sections(q))
        passed += ok
        print("PASS" if ok else "FAIL", q)
    print(f"{passed} of {len(QUESTIONS)} visible tests passed")
