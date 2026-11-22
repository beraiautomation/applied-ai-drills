"""A simulated LLM judge. Don't edit this file: the checker uses its own copy.

It behaves like a real judge model, with the same habits real judges have:

- It compares two answers and replies in text. It's asked to end with [[A]], [[B]] or [[C]]
  (C means a tie), but it doesn't always follow the format.
- Without a reference answer, it can't tell which answer is correct, so it prefers the
  longer one.
- When the two answers are about equally good, it picks whichever one it saw first.
- Now and then it replies without giving a verdict at all.

It's deterministic: the same inputs and the same call number always give the same reply.
"""
from __future__ import annotations

import hashlib
import re

_WORDS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8,
          "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20, "thirty": 30,
          "forty": 40, "forty-five": 45, "fifty": 50, "sixty": 60, "ninety": 90, "hundred": 100}
_STOP = set("a an the is are was be to of in on at for and or it its it's you your we our they their this that "
            "with from by as can only also per each any all do does not no yes".split())


_TIME = re.compile(r"\b(\d{1,2}):(\d{2})\s*(am|pm)?\b|\b(\d{1,2})\s*(am|pm)\b")


def _facts(text):
    """Every number in the text, normalized: "$1,450" is 1450, "two" is 2, "6pm" and "18:00" are 18."""
    text = text.lower()
    out = set()

    def time(m):
        hour = float(m.group(1) or m.group(4))
        minute = float(m.group(2) or 0)
        ampm = m.group(3) or m.group(5)
        if ampm == "pm" and hour < 12:
            hour += 12
        out.add(hour + minute / 100)
        return " "

    rest = _TIME.sub(time, text)
    for raw in re.findall(r"\d[\d,]*(?:\.\d+)?", rest):
        out.add(float(raw.replace(",", "")))
    for w in re.findall(r"[a-z]+(?:-[a-z]+)?", rest):
        if w in _WORDS:
            out.add(float(_WORDS[w]))
    return out


def _key_words(text):
    return {w for w in re.findall(r"[a-z]+", text.lower()) if w not in _STOP and len(w) >= 2}


def _polarity(text):
    t = text.strip().lower()
    if re.match(r"^(no|nope)\b", t) or " can't " in f" {t} " or " cannot " in f" {t} " or "never" in t:
        return "no"
    if re.match(r"^(yes|yep|sure)\b", t):
        return "yes"
    return None


def _score_with_reference(question, answer, reference):
    """0 to 10, the way a careful judge reads it when it has the reference."""
    if not answer.strip():
        return 0
    if re.search(r"\b(don't know|not sure|contact (support|the store))\b", answer.lower()):
        return 1
    ref_pol, ans_pol = _polarity(reference), _polarity(answer)
    if ref_pol and ans_pol and ref_pol != ans_pol:
        return 0
    ref_nums, ans_nums, q_nums = _facts(reference), _facts(answer), _facts(question)
    if ans_nums - ref_nums - q_nums:
        return 3                                   # adds a number the reference doesn't have
    if ref_nums:
        return 10 if ref_nums <= ans_nums else 4   # the numbers are the facts that matter
    words = _key_words(reference)
    overlap = len(words & _key_words(answer)) / max(1, len(words))
    return 10 if overlap >= 0.3 else 4


def _score_without_reference(answer):
    """No reference: it can't check facts, so longer looks better."""
    return len(answer.split())


_FORMATS = {
    "A": ["[[A]]",
          "Answer A is clearer and more complete. [[A]]",
          "Answer B is shorter, but Answer A gives the customer what they asked for. Final verdict: [[A]]",
          "Verdict: A",
          "**Winner: Answer A**",
          "I prefer the first answer.\n\nFinal answer: A",
          "winner: a"],
    "B": ["[[B]]",
          "Answer B is clearer and more complete. [[B]]",
          "Answer A is shorter, but Answer B gives the customer what they asked for. Final verdict: [[B]]",
          "Verdict: B",
          "**Winner: Answer B**",
          "I prefer the second answer.\n\nFinal answer: B",
          "winner: b"],
}
_TIE = ["Both answers give the same facts. [[C]]",
        "It's a tie: both are correct and complete."]
_NO_VERDICT = ["I can't compare these answers without more context about the store.",
               "Both answers have strengths. Answer A is direct and Answer B is friendly."]


class JudgeModel:
    """Call judge(question, answer_a, answer_b, reference=None). Returns the judge's reply as text."""

    def __init__(self):
        self.calls = 0
        self._seen = {}

    def judge(self, question, answer_a, answer_b, reference=None):
        self.calls += 1
        if self.calls > 500:
            raise RuntimeError("judge called more than 500 times")
        key = (question, answer_a, answer_b, reference)
        attempt = self._seen.get(key, 0)
        self._seen[key] = attempt + 1

        if reference:
            sa = _score_with_reference(question, answer_a, reference)
            sb = _score_with_reference(question, answer_b, reference)
            close = abs(sa - sb) < 1
        else:
            sa, sb = _score_without_reference(answer_a), _score_without_reference(answer_b)
            close = abs(sa - sb) <= 2
        winner = "A" if (close or sa > sb) else "B"   # close call: it picks the one it saw first

        h = int(hashlib.sha256(repr(key).encode("utf-8")).hexdigest(), 16)
        if (h + attempt) % 9 == 4:
            return _NO_VERDICT[(h // 9) % len(_NO_VERDICT)]
        if reference and sa == sb and (h // 5 + attempt) % 3 == 0:
            return _TIE[(h // 11) % len(_TIE)]     # sometimes it does call a tie
        options = _FORMATS[winner]
        return options[(h // 7 + attempt) % len(options)]
