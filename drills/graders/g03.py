"""Grader for drill 3: safe tool calls."""
from __future__ import annotations

import json
from pathlib import Path

from .common import Check, load, score_cases, unchanged, visible_tests


def c(name, raw=None, **args):
    return {"name": name, "arguments": raw if raw is not None else json.dumps(args)}


def grade(folder: Path, original: Path) -> list:
    checks = [unchanged(folder, original, "test_tools.py"), visible_tests(folder, "test_tools.py")]
    try:
        execute = load(folder, "tools").execute
    except Exception as exc:  # noqa: BLE001
        return checks + [Check("tools.py loads", False, str(exc)[:150])]

    def run(call):
        try:
            return execute(call), None
        except Exception as exc:  # noqa: BLE001
            return None, f"raised {type(exc).__name__} instead of returning an error"

    good = [
        ("get an order", (c("get_order", order_id="ORD-1044"), lambda r: r["result"]["total"] == 1200.0)),
        ("refund part of an order", (c("refund", order_id="ORD-1042", amount=20), lambda r: r["result"]["refunded"] == 20)),
        ("refund the full total", (c("refund", order_id="ORD-1043", amount=25), lambda r: r["result"]["refunded"] == 25)),
        ("refund with a reason", (c("refund", order_id="ORD-1042", amount=5, reason="late"), lambda r: r["result"]["reason"] == "late")),
        ("amount sent as text", (c("refund", order_id="ORD-1042", amount="12.50"), lambda r: r["result"]["refunded"] == 12.5)),
        ("convert currency", (c("convert_currency", amount=100, from_currency="USD", to_currency="EUR"), lambda r: r["result"]["amount"] == 92.0)),
    ]

    def ok_case(case):
        call, test = case
        r, err = run(call)
        if err:
            return err
        if not isinstance(r, dict) or r.get("ok") is not True:
            return f"returned {r}"
        return None if test(r) else f"wrong result {r.get('result')}"

    checks.append(score_cases("good calls still work", good, ok_case))

    bad = [
        ("arguments are not JSON", (c("get_order", raw="{order_id: ORD-1042"), None)),
        ("arguments are a list", (c("get_order", raw="[1, 2]"), None)),
        ("unknown tool", (c("wire_money", amount=10), "wire_money")),
        ("missing order_id", (c("refund", amount=10), "order_id")),
        ("missing amount", (c("refund", order_id="ORD-1042"), "amount")),
        ("extra unknown field", (c("get_order", order_id="ORD-1042", include_card=True), "include_card")),
        ("order_id wrong format", (c("get_order", order_id="1042"), "order_id")),
        ("order_id wrong type", (c("get_order", order_id=1042), "order_id")),
        ("order does not exist", (c("get_order", order_id="ORD-9999"), "order_id")),
        ("amount is a word", (c("refund", order_id="ORD-1042", amount="ten"), "amount")),
        ("amount is true", (c("refund", order_id="ORD-1042", amount=True), "amount")),
        ("amount is zero", (c("refund", order_id="ORD-1042", amount=0), "amount")),
        ("amount is negative", (c("refund", order_id="ORD-1042", amount=-5), "amount")),
        ("refund more than the total", (c("refund", order_id="ORD-1043", amount=25.01), "amount")),
        ("currency not allowed", (c("convert_currency", amount=5, from_currency="USD", to_currency="JPY"), "to_currency")),
        ("reason is not text", (c("refund", order_id="ORD-1042", amount=5, reason=42), "reason")),
    ]

    def bad_case(case):
        call, field = case
        r, err = run(call)
        if err:
            return err
        if not isinstance(r, dict) or r.get("ok") is not False:
            return f"accepted it: {r}"
        msg = str(r.get("error", ""))
        if not msg:
            return "no error message"
        if field and field not in msg:
            return f'error doesn\'t name "{field}": {msg[:60]}'
        return None

    checks.append(score_cases("bad calls return a clear error, never a crash", bad, bad_case))
    return checks
