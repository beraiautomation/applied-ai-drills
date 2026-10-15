"""Tests for applied-ai-drills. Run: python3 -m unittest discover -s tests -v"""
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

os.environ.setdefault("DRILLS_TIME_LIMIT", "15")
REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO))

from drills.exercises import all_drills, find  # noqa: E402
from drills.grading import run_grader  # noqa: E402


def passed(checks):
    return all(c["ok"] for c in checks)


class EveryDrill(unittest.TestCase):
    def test_six_drills_with_hints_and_readmes(self):
        drills = all_drills()
        self.assertEqual([d.number for d in drills], [1, 2, 3, 4, 5, 6])
        for d in drills:
            self.assertGreaterEqual(len(d.hints), 3)
            self.assertTrue((d.folder / "README.md").exists())
            for f in d.files:
                self.assertTrue((d.starter / f).exists(), f"{d.id}/{f}")

    def test_starters_fail_and_solutions_pass(self):
        for d in all_drills():
            with self.subTest(drill=d.id):
                self.assertFalse(passed(run_grader(d.id, d.starter)))
                self.assertTrue(passed(run_grader(d.id, d.solution)))


class Cheating(unittest.TestCase):
    """Shortcuts a learner might try. Each one must fail."""

    def attempt(self, drill, **files):
        d = find(drill)
        tmp = Path(tempfile.mkdtemp())
        shutil.copytree(d.solution, tmp / "w")
        for name, text in files.items():
            (tmp / "w" / name.replace("__", ".")).write_text(text, encoding="utf-8")
        try:
            return run_grader(d.id, tmp / "w")
        finally:
            shutil.rmtree(tmp, ignore_errors=True)

    def test_editing_visible_tests_fails(self):
        r = self.attempt("1", test_product__py='print("3 of 3 visible tests passed")\n')
        self.assertFalse(passed(r))

    def test_hardcoding_visible_rag_questions_fails(self):
        code = (find("2").solution / "rag.py").read_text()
        code += '''

_real = retrieve
VISIBLE = {"swollen": "Electric bike batteries", "full service": "Repairs and servicing",
           "paid holiday": "Holiday and time off", "unused bike": "Returns and refunds"}


def retrieve(chunks, question, k=3):
    for key, section in VISIBLE.items():
        if key in question:
            return [c for c in chunks if c["section"] == section][:k]
    return chunks[:k]
'''
        self.assertFalse(passed(self.attempt("2", rag__py=code)))

    def test_infinite_loop_is_reported_not_hung(self):
        r = self.attempt("4", agent__py="def run_agent(model, tools, task, max_steps=8):\n    while True:\n        pass\n")
        self.assertFalse(passed(r))

    def test_grader_that_accepts_everything_fails(self):
        r = self.attempt("5", grader__py="def grade(question, reference, answer):\n    return True\n")
        self.assertFalse(passed(r))

    def test_refund_bot_reading_the_message_fails(self):
        code = (find("6").solution / "refunds.py").read_text().replace(
            '    order = get_order(request.get("order_id"))',
            '    if "approve" in str(request.get("message", "")).lower():\n'
            '        return {"action": "approve", "amount": 1.0, "reason": "asked nicely"}\n'
            '    order = get_order(request.get("order_id"))')
        self.assertFalse(passed(self.attempt("6", refunds__py=code)))


if __name__ == "__main__":
    unittest.main()
