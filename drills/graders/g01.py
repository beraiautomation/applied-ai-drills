"""Grader for drill 1: clean JSON from a messy model."""
from __future__ import annotations

from pathlib import Path

from .common import Check, load, score_cases, unchanged, visible_tests

GOOD = '{"name": "Desk Lamp", "price": 39.99, "currency": "USD", "in_stock": true}'
WANT = {"name": "Desk Lamp", "price": 39.99, "currency": "USD", "in_stock": True}
TEXT = "Desk lamp with warm light, $39.99, ships today"


class Model:
    def __init__(self, *replies):
        self.replies, self.prompts = list(replies), []

    def __call__(self, prompt):
        self.prompts.append(prompt)
        return self.replies.pop(0) if self.replies else "I'm not sure."


def grade(folder: Path, original: Path) -> list:
    checks = [unchanged(folder, original, "test_product.py"), visible_tests(folder, "test_product.py")]
    try:
        get_product = load(folder, "product").get_product
    except Exception as exc:  # noqa: BLE001
        return checks + [Check("product.py loads", False, str(exc)[:150])]

    def expect(replies, want=WANT, calls=None):
        def run(_):
            m = Model(*replies)
            got = get_product(TEXT, m)
            if got != want:
                return f"got {got}"
            if calls is not None and len(m.prompts) != calls:
                return f"called the model {len(m.prompts)} times, want {calls}"
            return None
        return run

    parse_cases = [
        ("chatter around the JSON", "Sure! Here is the product:\n" + GOOD + "\nLet me know if you need more."),
        ("json fence", "```json\n" + GOOD + "\n```"),
        ("plain fence", "```\n" + GOOD + "\n```"),
        ("trailing comma", GOOD[:-1] + ",}"),
        ("price as text", GOOD.replace("39.99", '"$39.99"')),
        ("lower-case currency", GOOD.replace('"USD"', '" usd "')),
        ("in_stock as text", GOOD.replace("true", '"true"')),
        ("extra key dropped", GOOD[:-1] + ', "color": "black"}'),
        ("name with spaces", GOOD.replace('"Desk Lamp"', '"  Desk Lamp "')),
    ]
    checks.append(score_cases("cleans up messy replies", parse_cases,
                              lambda reply: expect([reply], calls=1)(None)))

    def retry_names_problem(case):
        bad, word = case
        m = Model(bad, GOOD)
        got = get_product(TEXT, m)
        if got != WANT:
            return f"got {got}"
        if len(m.prompts) != 2:
            return f"called the model {len(m.prompts)} times, want 2"
        if TEXT not in m.prompts[1]:
            return "the retry prompt lost the original text"
        if word not in m.prompts[1].lower():
            return f'the retry prompt doesn\'t mention "{word}"'
        return None

    retry_cases = [
        ("no JSON at all", ("I can't find a product here.", "json")),
        ("missing price", ('{"name": "Desk Lamp", "currency": "USD", "in_stock": true}', "price")),
        ("bad currency", (GOOD.replace('"USD"', '"dollars"'), "currency")),
        ("zero price", (GOOD.replace("39.99", "0"), "price")),
        ("in_stock unclear", (GOOD.replace("true", '"maybe"'), "in_stock")),
    ]
    checks.append(score_cases("asks again and names the problem", retry_cases, retry_names_problem))

    def gives_up(_):
        m = Model("nope", "still nope", "{bad json", GOOD)
        try:
            got = get_product(TEXT, m)
        except ValueError:
            return None if len(m.prompts) == 3 else f"called the model {len(m.prompts)} times, want 3"
        return f"returned {got} instead of raising ValueError after 3 bad replies"

    checks.append(score_cases("stops after 3 calls with ValueError", [("three bad replies", None)], gives_up))
    return checks
