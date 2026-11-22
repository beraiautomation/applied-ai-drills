"""Grader for drill 7: an LLM judge you can trust. Uses its own copy of the judge model."""
from __future__ import annotations

from pathlib import Path

from .common import Check, load, score_cases, unchanged, visible_tests

# (question, reference, answer_a, answer_b, human, kind)
HIDDEN = [
    # same facts, different words: a tie
    ("How much does a full service cost?", "A full service costs 95 pounds.",
     "It's £95.", "A full service is 95 pounds.", "tie", "tie"),
    ("When does the store close on Sundays?", "It closes at 16:00.",
     "We close at 4pm on Sundays.", "16:00.", "tie", "tie"),
    ("How many days of holiday do full-time staff get?", "28 days a year, including public holidays.",
     "You get 28 days a year, public holidays included.", "28 days, including public holidays.", "tie", "tie"),
    ("Can members cancel any time?", "Yes, from their online account.",
     "Yes, they can cancel from their online account.", "Yes, any time, from the online account.", "tie", "tie"),
    ("What's the staff discount on bikes?", "30 percent off bikes.",
     "Staff get 30% off bikes.", "30 percent off any bike.", "tie", "tie"),
    ("Who can approve a refund outside the rules?", "Only a manager can approve it.",
     "Only a manager.", "You need a manager to approve it.", "tie", "tie"),
    ("Do we deliver bikes outside the UK?", "No, bikes are only delivered in the UK.",
     "No, only within the UK.", "No. We only deliver bikes in the UK.", "tie", "tie"),
    ("When does the morning shift start?", "Morning shifts start at 6:30.",
     "At 6:30.", "The morning shift starts at 6:30am.", "tie", "tie"),
    # short and correct against long and wrong
    ("How much does a basic service cost?", "A basic service costs 45 pounds.",
     "45 pounds.", "A basic service at Northwind is great value and costs 55 pounds, which includes a full safety "
     "check of your bike.", "A", "length"),
    ("How long do I have to return an unused bike?", "30 days from purchase.",
     "Thanks for asking! You can return an unused bike within 14 days of buying it, as long as you have the "
     "receipt with you.", "30 days.", "B", "length"),
    ("What time does the Leeds store close?", "It closes at 18:00.",
     "6pm.", "Our Leeds store is open late most days and closes at 8pm, so there's plenty of time to visit after "
     "work.", "A", "length"),
    ("How many free services do members get?", "Two free basic services a year.",
     "Members get one free basic service each year, plus a discount on parts and a priority booking slot in the "
     "workshop.", "Two free basic services a year.", "B", "length"),
    ("How much is the Commuter E2?", "The Commuter E2 costs $1,450.",
     "$1,450.", "The Commuter E2 is our most popular electric bike for city riding, and it costs $1,540 with a "
     "two-year warranty.", "A", "length"),
    ("How long do refunds take?", "Within 5 working days.",
     "Refunds can take a little while because they go back through the bank, so please allow up to 10 working "
     "days.", "Within 5 working days.", "B", "length"),
    ("Can I return a bike I've ridden?", "No. Ridden bikes can only be exchanged for store credit.",
     "No, but you can get store credit.", "Yes, of course. We accept returns on ridden bikes for a full refund to "
     "your card, no questions asked.", "A", "length"),
    ("What is the staff discount on clothing?", "40 percent off clothing.",
     "Staff get a generous discount on clothing in both stores, which is currently 25 percent off the ticket "
     "price.", "40% off clothing.", "B", "length"),
    # correct against correct plus a made-up number
    ("How much does a full service cost?", "A full service costs 95 pounds.",
     "A full service costs 95 pounds and takes 2 hours.", "It's £95.", "B", "made_up"),
    ("How much do online orders need to cost for free delivery?", "Orders over 500 pounds get free delivery.",
     "Free delivery on orders over £500.", "Orders over £500 get free delivery, and it arrives in 1 day.", "A",
     "made_up"),
    ("Who can approve a refund outside the rules?", "Only a manager can approve it.",
     "A manager, for refunds up to $200.", "Only a manager can approve it.", "B", "made_up"),
    ("How much is Northwind Care?", "9 pounds a month.",
     "£9 a month.", "£9 a month, or £90 if you pay for the year.", "A", "made_up"),
    ("When does the store open on Sundays?", "At 10:00 on Sundays.",
     "10am on Sundays, and 9am in the summer.", "At 10am on Sundays.", "B", "made_up"),
    # complete against missing the key fact
    ("How long do refunds take?", "Within 5 working days.",
     "Refunds take a few days.", "They take up to 5 working days.", "B", "missing"),
    ("What's the staff discount on bikes?", "30 percent off bikes.",
     "Staff get 30% off bikes.", "Staff get a discount on bikes.", "A", "missing"),
    ("How long does a bike fitting take?", "45 minutes.",
     "A bike fitting doesn't take long at all.", "About 45 minutes.", "B", "missing"),
    # opposite meaning
    ("Is the store open on 25 December?", "No, both stores are closed on 25 and 26 December.",
     "No, we're closed on 25 and 26 December.", "Yes, it's open on 25 December.", "A", "opposite"),
    ("Can staff open a battery case?", "No, staff must never open a battery case.",
     "Yes, staff can open a battery case if they're careful and wear gloves.", "No, never open a battery case.",
     "B", "opposite"),
    ("Can members cancel any time?", "Yes, from their online account.",
     "Yes, from their online account.", "No, members can't cancel early.", "A", "opposite"),
    # not an answer
    ("Where should a swollen battery go?", "In the metal fire box in the workshop.",
     "I'm not sure, please contact support for help with batteries.", "In the metal fire box in the workshop.",
     "B", "non_answer"),
    ("When does the morning shift start?", "Morning shifts start at 6:30.",
     "Morning shifts start at 6:30.", "I don't know, sorry.", "A", "non_answer"),
    ("How much does a full service cost?", "A full service costs 95 pounds.",
     "I don't know the exact price, so please contact the store and they'll tell you.", "95 pounds.", "B",
     "non_answer"),
]

PARSE = [
    ("[[A]]", "A"), ("[[b]]", "B"), ("[[ B ]]", "B"), ("[[C]]", "tie"), ("[[tie]]", "tie"),
    ("Answer A is shorter, but Answer B gives the customer what they asked for. Final verdict: [[B]]", "B"),
    ("At first I leaned to [[A]], but after checking the price again: [[B]]", "B"),
    ("Verdict: A", "A"), ("verdict: b", "B"), ("**Winner: Answer B**", "B"), ("**Final verdict:** A", "A"),
    ("**Final verdict**: B", "B"), ("I prefer the second answer.\n\nFinal answer: B", "B"), ("winner: a", "A"),
    ("Winner - Answer A", "A"), ("Verdict: tie", "tie"), ("It's a tie: both are correct and complete.", "tie"),
    ("Both answers are equally good.", "tie"),
    ("I can't compare these answers without more context about the store.", None),
    ("Both answers have strengths. Answer A is direct and Answer B is friendly.", None),
    ("Answer A is wrong. Answer B is right.", None),
    ("ABSOLUTELY. Both look fine to me.", None),
    ("", None), (None, None),
]

TARGET = 0.90


def flip(w):
    return {"A": "B", "B": "A"}.get(w, w)


class Spy:
    """Wraps the real judge model and records every call."""

    def __init__(self, model):
        self.model, self.refs = model, []

    @property
    def calls(self):
        return self.model.calls

    def judge(self, question, answer_a, answer_b, reference=None):
        self.refs.append(reference)
        return self.model.judge(question, answer_a, answer_b, reference=reference)


class Script:
    """A judge that replies from a script, to test retries."""

    def __init__(self, *replies):
        self.replies, self.calls = list(replies), 0

    def judge(self, question, answer_a, answer_b, reference=None):
        self.calls += 1
        if self.calls > 20:
            raise RuntimeError("judge called more than 20 times for one pair")
        return self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]


def grade(folder: Path, original: Path) -> list:
    checks = [unchanged(folder, original, "test_judge.py"), unchanged(folder, original, "judge_model.py"),
              unchanged(folder, original, "labeled.json"), visible_tests(folder, "test_judge.py")]
    try:
        mod = load(folder, "judge")
        parse, pair, measure = mod.parse_verdict, mod.judge_pair, mod.measure
    except Exception as exc:  # noqa: BLE001
        return checks + [Check("judge.py loads", False, str(exc)[:150])]
    JudgeModel = load(original, "judge_model").JudgeModel  # the checker's own copy

    def parse_case(case):
        text, want = case
        got = parse(text)
        return None if got == want else f"got {got!r}, want {want!r}"

    checks.append(score_cases("reads the judge's verdict",
                              [(repr(t)[:40], (t, w)) for t, w in PARSE], parse_case))

    # one run over the hidden pairs, with a fresh model per pair
    results, calls, no_ref, crashed = [], [], 0, None
    for q, ref, a, b, human, kind in HIDDEN:
        spy = Spy(JudgeModel())
        try:
            r = pair(spy, q, a, b, ref)
            winner = r.get("winner") if isinstance(r, dict) else None
        except Exception as exc:  # noqa: BLE001
            winner, crashed = None, crashed or f"{type(exc).__name__}: {exc}"[:120]
        results.append((q, a, b, human, kind, winner))
        calls.append(spy.calls)
        no_ref += any(x != ref for x in spy.refs)
    if crashed:
        checks.append(Check("judge_pair runs", False, crashed))

    checks.append(Check("gives the judge the reference", no_ref == 0,
                        "every call had it" if not no_ref else f"{no_ref} of {len(HIDDEN)} pairs judged without it"))
    over = max(calls) if calls else 0
    checks.append(Check("at most 4 judge calls per pair", 0 < over <= 4,
                        f"most calls for one pair: {over}" if over else "the judge was never called"))

    def order_case(row):
        q, ref, a, b = row
        one = pair(JudgeModel(), q, a, b, ref)["winner"]
        two = pair(JudgeModel(), q, b, a, ref)["winner"]
        return None if one == flip(two) else f"{one} one way, {two} the other"

    checks.append(score_cases("same winner when the answers swap places",
                              [(q[:30], (q, ref, a, b)) for q, ref, a, b, _, _ in HIDDEN], order_case))

    right = sum(w == h for _, _, _, h, _, w in results)
    score = right / len(HIDDEN)
    miss = next((f'"{q[:35]}" got {w}, want {h}' for q, _, _, h, _, w in results if w != h), "")
    checks.append(Check("agrees with human labels", score >= TARGET,
                        f"{round(score * 100)}% (need {round(TARGET * 100)}%)" + (f" · e.g. {miss}" if miss else "")))
    wrong_pick = [q for q, _, _, h, k, w in results if h in ("A", "B") and w == flip(h)]
    checks.append(Check("never picks the wrong answer", not wrong_pick,
                        "never did" if not wrong_pick else f'picked the wrong one for "{wrong_pick[0][:40]}"'))

    def retry_case(case):
        replies, want, want_conf, max_calls = case
        m = Script(*replies)
        r = pair(m, "Q?", "first", "second", "ref")
        if r.get("winner") != want or r.get("confident") is not want_conf:
            return f"got {r.get('winner')}/confident={r.get('confident')}, want {want}/{want_conf}"
        if m.calls > max_calls:
            return f"{m.calls} calls"
        return None

    retry = [
        ("no verdict, then one", (["I can't decide.", "[[A]]", "[[B]]"], "A", True, 3)),
        ("both orders agree", (["[[B]]", "[[A]]"], "B", True, 2)),
        ("it just picks the first", (["[[A]]", "[[A]]"], "tie", False, 2)),
        ("never a verdict", (["Hmm, hard to say."], "tie", False, 4)),
        ("tie both ways", (["[[C]]", "Verdict: tie"], "tie", True, 2)),
    ]
    checks.append(score_cases("handles position bias and missing verdicts", retry, retry_case))

    def fake(answers):
        it = iter(answers)
        return lambda q, a, b, ref: {"winner": next(it), "confident": True}

    def rows(humans):
        return [{"question": f"q{i}", "reference": "r", "answer_a": "a", "answer_b": "b", "human": h}
                for i, h in enumerate(humans)]

    def measure_case(case):
        humans, judged, kwargs, want_agree, want_trust = case
        r = measure(fake(judged), rows(humans), **kwargs)
        if r.get("n") != len(humans):
            return f"n={r.get('n')}, want {len(humans)}"
        if abs(float(r.get("agreement", -1)) - want_agree) > 1e-9:
            return f"agreement={r.get('agreement')}, want {want_agree}"
        if r.get("trusted") is not want_trust:
            return f"trusted={r.get('trusted')}, want {want_trust}"
        return None

    h25 = ["A", "B", "tie", "B", "A"] * 5
    j20 = h25[:20] + [flip(x) if x != "tie" else "A" for x in h25[20:]]
    j19 = h25[:19] + [flip(x) if x != "tie" else "A" for x in h25[19:]]
    measure_cases = [
        ("20 of 25 right", (h25, j20, {}, 0.8, True)),
        ("19 of 25 right", (h25, j19, {}, 0.76, False)),
        ("10 of 10 right, too few", (h25[:10], h25[:10], {}, 1.0, False)),
        ("min_labels=5 is respected", (h25[:10], h25[:10], {"min_labels": 5}, 1.0, True)),
        ("ties count", (["tie"] * 20 + ["A"] * 5, ["tie"] * 20 + ["B"] * 5, {}, 0.8, True)),
        ("a judge that always says tie", (h25, ["tie"] * 25, {}, 0.2, False)),
        ("no labels at all", ([], [], {}, 0.0, False)),
    ]
    checks.append(score_cases("measures the judge honestly", measure_cases, measure_case))

    try:
        same = all(pair(JudgeModel(), q, a, b, ref) == pair(JudgeModel(), q, a, b, ref)
                   for q, ref, a, b, _, _ in HIDDEN[:8])
    except Exception:  # noqa: BLE001
        same = False
    checks.append(Check("same result every time", same, ""))
    return checks
