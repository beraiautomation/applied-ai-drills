"""A few checks to get you started. Run: python3 test_judge.py"""
import json
from pathlib import Path

from judge import judge_pair, measure, parse_verdict
from judge_model import JudgeModel

LABELED = json.loads((Path(__file__).parent / "labeled.json").read_text(encoding="utf-8"))
ROW = {r["answer_b"]: r for r in LABELED}


def flip(winner):
    return {"A": "B", "B": "A"}.get(winner, winner)


def t_marker():
    return parse_verdict("[[B]]") == "B"


def t_last_marker_wins():
    text = "Answer B is shorter, but Answer A gives the customer what they asked for. Final verdict: [[A]]"
    return parse_verdict(text) == "A"


def t_tie():
    return parse_verdict("Both answers give the same facts. [[C]]") == "tie"


def t_no_verdict():
    return parse_verdict("I can't compare these answers without more context about the store.") is None


def t_same_winner_when_swapped():
    r = ROW["It closes at 6pm."]
    m = JudgeModel()
    one = judge_pair(m, r["question"], r["answer_a"], r["answer_b"], r["reference"])
    two = judge_pair(m, r["question"], r["answer_b"], r["answer_a"], r["reference"])
    return one["winner"] == flip(two["winner"])


def t_short_correct_beats_long_wrong():
    r = ROW["45 pounds."]
    return judge_pair(JudgeModel(), r["question"], r["answer_a"], r["answer_b"], r["reference"])["winner"] == "B"


def t_measure_counts_every_row():
    always_tie = lambda q, a, b, ref: {"winner": "tie", "confident": False}  # noqa: E731
    r = measure(always_tie, LABELED)
    return r["n"] == 12 and abs(r["agreement"] - 3 / 12) < 1e-9 and r["trusted"] is False


def t_twelve_labels_is_not_enough():
    m = JudgeModel()
    r = measure(lambda q, a, b, ref: judge_pair(m, q, a, b, ref), LABELED)
    return r["n"] == 12 and r["trusted"] is False


TESTS = [t_marker, t_last_marker_wins, t_tie, t_no_verdict, t_same_winner_when_swapped,
         t_short_correct_beats_long_wrong, t_measure_counts_every_row, t_twelve_labels_is_not_enough]

if __name__ == "__main__":
    passed = 0
    for t in TESTS:
        try:
            ok = t() is True
        except Exception as exc:  # noqa: BLE001
            ok = False
            print(f"     {type(exc).__name__}: {exc}")
        passed += ok
        print("PASS" if ok else "FAIL", t.__name__[2:].replace("_", " "))
    print(f"{passed} of {len(TESTS)} visible tests passed")
