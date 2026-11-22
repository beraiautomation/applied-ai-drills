"""Use an LLM judge to compare two answers, and measure whether the judge can be trusted."""
import re

_MARKER = re.compile(r"\[\[\s*(a|b|c|tie)\s*\]\]", re.IGNORECASE)
_LABELED = re.compile(
    r"\b(?:final\s+verdict|verdict|winner|final\s+answer)\**\s*[:\-]\s*\**\s*(?:answer\s+)?(a|b|tie)\b",
    re.IGNORECASE)
_TIE = re.compile(r"\bit'?s a tie\b|\bequally good\b", re.IGNORECASE)


def parse_verdict(text):
    """Return "A", "B", "tie", or None when the reply has no clear verdict."""
    if not isinstance(text, str):
        return None
    for pattern in (_MARKER, _LABELED):
        found = pattern.findall(text)
        if found:
            last = found[-1].lower()
            return "tie" if last in ("c", "tie") else last.upper()
    if _TIE.search(text):
        return "tie"
    return None


def _ask(model, question, first, second, reference):
    """One order, with one retry if the reply has no verdict."""
    calls, verdict = 0, None
    for _ in range(2):
        calls += 1
        verdict = parse_verdict(model.judge(question, first, second, reference=reference))
        if verdict is not None:
            break
    return verdict, calls


def judge_pair(model, question, answer_a, answer_b, reference=None):
    """Return {"winner": "A" | "B" | "tie", "confident": bool}."""
    straight, _ = _ask(model, question, answer_a, answer_b, reference)
    swapped, _ = _ask(model, question, answer_b, answer_a, reference)
    swapped = {"A": "B", "B": "A"}.get(swapped, swapped)
    if straight is not None and straight == swapped:
        return {"winner": straight, "confident": True}
    return {"winner": "tie", "confident": False}


def measure(judge, labeled, min_labels=20):
    """Compare the judge with human labels. Return {"agreement": float, "n": int, "trusted": bool}."""
    n = len(labeled)
    if n == 0:
        return {"agreement": 0.0, "n": 0, "trusted": False}
    agree = 0
    for row in labeled:
        got = judge(row["question"], row["answer_a"], row["answer_b"], row.get("reference"))
        agree += got.get("winner") == row["human"]
    agreement = agree / n
    return {"agreement": agreement, "n": n, "trusted": n >= min_labels and agreement >= 0.8}
