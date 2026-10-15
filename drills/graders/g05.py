"""Grader for drill 5: an eval that catches wrong answers. Uses a hidden labeled set."""
from __future__ import annotations

from pathlib import Path

from .common import Check, load, unchanged, visible_tests

# (question, reference, answer, correct, kind)
HIDDEN = [
    # correct, in different words
    ("How much does a full service cost?", "A full service costs 95 pounds.", "It's £95.", True, "paraphrase"),
    ("How much does a full service cost?", "A full service costs 95 pounds.", "95 pounds for the full service.", True, "paraphrase"),
    ("How much do online orders need to cost for free delivery?", "Orders over 500 pounds get free delivery.", "Free delivery starts above £500.", True, "paraphrase"),
    ("What's the price of the e-bike?", "The Commuter E2 costs $1,450.", "It's 1450 dollars.", True, "paraphrase"),
    ("What's the price of the e-bike?", "The Commuter E2 costs $1,450.", "The Commuter E2 is $1,450.00.", True, "paraphrase"),
    ("How many days of holiday do full-time staff get?", "28 days a year, including public holidays.", "You get 28 days, public holidays included.", True, "paraphrase"),
    ("When does the morning shift start?", "Morning shifts start at 6:30.", "It starts at 6:30am.", True, "paraphrase"),
    ("When does the store open on Sundays?", "At 10:00 on Sundays.", "10am on Sunday.", True, "paraphrase"),
    ("When does the store close on Sundays?", "It closes at 16:00.", "We close at 4pm.", True, "paraphrase"),
    ("How many free services do members get?", "Two free basic services a year.", "Members get 2 free basic services every year.", True, "paraphrase"),
    ("What's the staff discount on bikes?", "30 percent off bikes.", "Staff get 30% off bikes.", True, "paraphrase"),
    ("How long does a bike fitting take?", "45 minutes.", "About forty-five minutes.", True, "paraphrase"),
    ("Who can approve a refund outside the rules?", "Only a manager can approve it.", "You need a manager to approve it.", True, "paraphrase"),
    ("Where should a swollen battery go?", "In the metal fire box in the workshop.", "Put it in the metal fire box in the workshop.", True, "paraphrase"),
    ("Do we deliver bikes outside the UK?", "No, bikes are only delivered in the UK.", "No, only within the UK.", True, "paraphrase"),
    ("Can members cancel any time?", "Yes, from their online account.", "Yes, they can cancel online at any time.", True, "paraphrase"),
    ("Is the store open on 25 December?", "No, both stores are closed on 25 and 26 December.", "No, we're closed on 25 and 26 December.", True, "paraphrase"),
    # wrong number or missing fact
    ("How much does a full service cost?", "A full service costs 95 pounds.", "A full service costs 85 pounds.", False, "wrong"),
    ("What's the price of the e-bike?", "The Commuter E2 costs $1,450.", "It's $1,540.", False, "wrong"),
    ("How many days of holiday do full-time staff get?", "28 days a year, including public holidays.", "25 days a year.", False, "wrong"),
    ("When does the store close on Sundays?", "It closes at 16:00.", "We close at 6pm.", False, "wrong"),
    ("When does the morning shift start?", "Morning shifts start at 6:30.", "It starts at 7:30.", False, "wrong"),
    ("How long do refunds take?", "Within 5 working days.", "Refunds take a few days.", False, "missing"),
    ("What's the staff discount on bikes?", "30 percent off bikes.", "Staff get a discount on bikes.", False, "missing"),
    # made-up details
    ("How much does a full service cost?", "A full service costs 95 pounds.", "It's £95 and takes 2 hours.", False, "made_up"),
    ("How much do online orders need to cost for free delivery?", "Orders over 500 pounds get free delivery.", "Over £500, and delivery takes 1 day.", False, "made_up"),
    ("How many days of holiday do full-time staff get?", "28 days a year, including public holidays.", "28 days, plus 5 extra days after 2 years.", False, "made_up"),
    ("Who can approve a refund outside the rules?", "Only a manager can approve it.", "A manager, for refunds up to $200.", False, "made_up"),
    ("How much is Northwind Care?", "9 pounds a month.", "£9 a month, or £90 a year.", False, "made_up"),
    ("Can members cancel any time?", "Yes, from their online account.", "Yes, with 30 days' notice.", False, "made_up"),
    ("When does the store open on Sundays?", "At 10:00 on Sundays.", "10am, and 9am in summer.", False, "made_up"),
    # opposite meaning
    ("Do we deliver bikes outside the UK?", "No, bikes are only delivered in the UK.", "Yes, we deliver bikes worldwide.", False, "opposite"),
    ("Can members cancel any time?", "Yes, from their online account.", "No, members can't cancel early.", False, "opposite"),
    ("Is the store open on 25 December?", "No, both stores are closed on 25 and 26 December.", "Yes, it's open on 25 December.", False, "opposite"),
    ("Can staff open a battery case?", "No, staff must never open a battery case.", "Staff can open it carefully.", False, "opposite"),
    ("Can staff open a battery case?", "No, staff must never open a battery case.", "Never open a battery case.", True, "paraphrase"),
    # not an answer
    ("How much does a full service cost?", "A full service costs 95 pounds.", "I don't know, sorry.", False, "non_answer"),
    ("Where should a swollen battery go?", "In the metal fire box in the workshop.", "Please contact support for help with batteries.", False, "non_answer"),
    ("When does the morning shift start?", "Morning shifts start at 6:30.", "", False, "non_answer"),
    ("Who can approve a refund outside the rules?", "Only a manager can approve it.", "I'm not sure who approves that.", False, "non_answer"),
]

TARGET = 0.90


def grade(folder: Path, original: Path) -> list:
    checks = [unchanged(folder, original, "test_grader.py"), unchanged(folder, original, "cases.json"),
              visible_tests(folder, "test_grader.py")]
    try:
        grade_fn = load(folder, "grader").grade
    except Exception as exc:  # noqa: BLE001
        return checks + [Check("grader.py loads", False, str(exc)[:150])]

    right, accepted_made_up, mistakes = 0, [], []
    for q, ref, ans, want, kind in HIDDEN:
        try:
            got = grade_fn(q, ref, ans)
        except Exception as exc:  # noqa: BLE001
            got = f"error: {type(exc).__name__}"
        if got is want:
            right += 1
        else:
            mistakes.append(f'"{ans}" (want {want})')
            if kind == "made_up" and got is True:
                accepted_made_up.append(ans)
    score = right / len(HIDDEN)
    detail = f"{round(score * 100)}% right (need {round(TARGET * 100)}%)"
    if mistakes:
        detail += " · e.g. " + mistakes[0]
    checks.append(Check("agrees with human labels", score >= TARGET, detail))
    checks.append(Check("never accepts a made-up detail", not accepted_made_up,
                        "caught every one" if not accepted_made_up else f'accepted: "{accepted_made_up[0]}"'))

    deterministic = all(grade_fn(q, r, a) == grade_fn(q, r, a) for q, r, a, _, _ in HIDDEN[:10])
    checks.append(Check("same result every time", deterministic, ""))
    return checks
