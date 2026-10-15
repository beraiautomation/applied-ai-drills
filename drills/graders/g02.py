"""Grader for drill 2: RAG retrieval. Uses hidden questions and a second, unseen document."""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from .common import Check, load, unchanged, visible_tests

CAFE = """# Harbor Cafe Team Guide

Practice document. Harbor Cafe is a made-up cafe by the sea.

## Shifts and breaks

Morning shifts start at 6:30 and end at 14:30. Afternoon shifts run from 12:00 to 20:00. Everyone working six hours or more gets a paid 30 minute break. Swap shifts only through the rota app, and tell the shift lead.

## Food safety

Wash hands before every shift and after handling raw eggs. Fridges must stay between 1 and 5 degrees, and the temperature is written on the chart at 8:00 and 15:00. Throw away cooked food after 3 days. Allergen labels must be on every cake in the display.

## Coffee recipes

A flat white uses a double shot and 150 ml of steamed milk. A latte uses a single shot and 220 ml of milk. Oat and soy milk cost 40 pence extra. Grind size is checked every morning with a test shot that should take 25 to 30 seconds.

## Tips

Card tips and cash tips are shared equally between everyone who worked that week. The shift lead counts cash tips every Sunday evening. Tips are paid with wages on the last Friday of the month.

## Opening and closing

The first person in turns off the alarm with the code card, switches on the espresso machine and checks the fridge temperatures. At closing, clean the steam wands, empty the grinders, mop the floor and lock the back door. The last person out sets the alarm.

## Customer allergies

If a customer has an allergy, tell them which items contain it using the allergen folder at the till. Never guess. If you are not sure, say so and offer something from the safe list. Nut-free cakes are made on Mondays in a separate kitchen.

## Uniform

Wear the navy apron and black non-slip shoes. Long hair must be tied back. Aprons are washed by the cafe, so leave them in the laundry bag on Friday.

## Loyalty card

Customers get one stamp per hot drink. After nine stamps, the tenth drink is free. Stamps can't be used for food. Lost cards can't be replaced.

## Accidents

Write every accident in the accident book, even small cuts or burns. The first aid kit is under the sink in the kitchen. For burns, cool the skin under running water for 20 minutes.

## Pay and payslips

Wages are paid monthly by bank transfer on the last Friday. Payslips are sent by email. Overtime is paid at one and a half times the normal rate when approved by the manager.
"""

HANDBOOK_HIDDEN = [
    ("When does the Leeds store open on Sundays?", "Opening hours"),
    ("Can accessories like a helmet be returned?", "Returns and refunds"),
    ("How fast do refunds reach the customer's card?", "Returns and refunds"),
    ("What does a basic service include?", "Repairs and servicing"),
    ("How much is the Northwind Care membership per month?", "Northwind Care membership"),
    ("What happens if a member's payment fails twice?", "Northwind Care membership"),
    ("At what temperature should batteries be stored?", "Electric bike batteries"),
    ("Is delivery free for big online orders?", "Delivery"),
    ("Do we ship bikes to Ireland?", "Delivery"),
    ("What discount do staff get on clothing?", "Staff discount"),
    ("How often can staff buy a discounted bike?", "Staff discount"),
    ("How early must I send a holiday request?", "Holiday and time off"),
    ("Who do I call when I am sick?", "Sick leave"),
    ("When do I need a doctor's note?", "Sick leave"),
    ("Do I have to wear safety glasses in the workshop?", "Uniform and safety gear"),
    ("How long is a bike fitting appointment?", "Bike fitting"),
    ("Who counts large amounts of cash?", "Cash and card payments"),
    ("What happens to phones left in the store?", "Lost property"),
    ("How quickly must a manager reply to a complaint?", "Customer complaints"),
    ("Can I give a refund outside the rules?", "Customer complaints"),
]

CAFE_HIDDEN = [
    ("What time does the morning shift start?", "Shifts and breaks"),
    ("How long is the paid break?", "Shifts and breaks"),
    ("What temperature should the fridges be?", "Food safety"),
    ("How long can cooked food be kept?", "Food safety"),
    ("How much milk goes in a flat white?", "Coffee recipes"),
    ("Does oat milk cost extra?", "Coffee recipes"),
    ("How are tips shared?", "Tips"),
    ("Who turns off the alarm in the morning?", "Opening and closing"),
    ("What do I tell a customer with a nut allergy?", "Customer allergies"),
    ("What shoes do I need to wear?", "Uniform"),
    ("How many stamps for a free drink?", "Loyalty card"),
    ("Where is the first aid kit?", "Accidents"),
    ("How should I treat a burn?", "Accidents"),
    ("When are wages paid?", "Pay and payslips"),
    ("Is overtime paid more?", "Pay and payslips"),
]

TARGET = 0.85


def _words(text):
    return re.findall(r"[A-Za-z0-9']+", text)


def _body_words(doc):
    return Counter(w for line in doc.splitlines() if not line.startswith("#") for w in _words(line))


def _check_chunks(chunk, doc, label):
    chunks = chunk(doc)
    problems = []
    if not isinstance(chunks, list) or not chunks:
        return [f"{label}: chunk() returned nothing"], []
    source = set(_words(doc))
    for c in chunks:
        if not {"id", "section", "text"} <= set(c):
            problems.append(f"{label}: a chunk is missing id, section or text")
            break
        if len(c["text"]) > 800:
            problems.append(f"{label}: chunk {c['id']} has {len(c['text'])} characters (max 800)")
            break
        cut = [w for w in _words(c["text"]) if w not in source]
        if cut:
            problems.append(f"{label}: chunk {c['id']} cuts a word: '{cut[0]}'")
            break
    covered = Counter(w for c in chunks for w in _words(c["text"]))
    lost = [w for w, n in _body_words(doc).items() if covered[w] < n]
    if lost:
        problems.append(f"{label}: text went missing, e.g. '{lost[0]}'")
    return problems, chunks


def _recall(retrieve, chunks, questions):
    misses = []
    for q, want in questions:
        top = retrieve(chunks, q, k=3)
        if not any(want.lower() == str(c.get("section", "")).strip().lower() for c in top[:3]):
            misses.append(q)
    return 1 - len(misses) / len(questions), misses


def grade(folder: Path, original: Path) -> list:
    checks = [unchanged(folder, original, "test_rag.py"), unchanged(folder, original, "handbook.md"),
              visible_tests(folder, "test_rag.py")]
    try:
        rag = load(folder, "rag")
    except Exception as exc:  # noqa: BLE001
        return checks + [Check("rag.py loads", False, str(exc)[:150])]
    handbook = (original / "handbook.md").read_text(encoding="utf-8")

    problems, hb_chunks = _check_chunks(rag.chunk, handbook, "handbook")
    p2, cafe_chunks = _check_chunks(rag.chunk, CAFE, "new document")
    problems += p2
    checks.append(Check("chunks are whole, complete and under 800 characters", not problems,
                        "every chunk is fine" if not problems else problems[0]))
    if not hb_chunks or not cafe_chunks:
        return checks

    for label, chunks, qs in (("handbook", hb_chunks, HANDBOOK_HIDDEN), ("a document you haven't seen", cafe_chunks, CAFE_HIDDEN)):
        try:
            score, misses = _recall(rag.retrieve, chunks, qs)
        except Exception as exc:  # noqa: BLE001
            checks.append(Check(f"finds the right section: {label}", False, f"{type(exc).__name__}: {exc}"[:150]))
            continue
        detail = f"{round(score * 100)}% in the top 3 (need {round(TARGET * 100)}%)"
        if misses:
            detail += f' · missed: "{misses[0]}"'
        checks.append(Check(f"finds the right section: {label}", score >= TARGET, detail))
    return checks
