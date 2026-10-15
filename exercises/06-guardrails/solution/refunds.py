"""Decide refund requests for the support bot. The rules live here, not in the prompt."""
import datetime as dt
import re

AUTO_APPROVE_LIMIT = 50.0
WINDOW_DAYS = 30


def _deny(reason):
    return {"action": "deny", "amount": None, "reason": reason}


def _amount(value):
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip().replace(",", "")
        if re.fullmatch(r"[$£€]?\s*\d+(\.\d{1,2})?", text):
            return float(re.sub(r"[^\d.]", "", text))
    return None


def decide_refund(request, get_order, today):
    """Return {"action": "approve" | "needs_human" | "deny", "amount": float or None, "reason": str}.

    The message is never used: customers (or text pasted into notes) can't talk their way past the rules.
    """
    order = get_order(request.get("order_id"))
    if not order:
        return _deny("order not found")
    if order.get("customer_id") != request.get("customer_id"):
        return _deny("order belongs to a different customer")
    try:
        age = (dt.date.fromisoformat(today) - dt.date.fromisoformat(order["date"])).days
    except (KeyError, TypeError, ValueError):
        return _deny("order date is missing or invalid")
    if age > WINDOW_DAYS:
        return _deny(f"order is {age} days old, the limit is {WINDOW_DAYS}")
    amount = _amount(request.get("amount"))
    if amount is None or amount <= 0:
        return _deny("amount must be a number above 0")
    left = round(float(order["total"]) - float(order.get("refunded_so_far") or 0), 2)
    if amount > left:
        return _deny(f"amount {amount:.2f} is more than the {left:.2f} left on this order")
    if amount <= AUTO_APPROVE_LIMIT:
        return {"action": "approve", "amount": amount, "reason": "within policy"}
    return {"action": "needs_human", "amount": amount, "reason": f"over {AUTO_APPROVE_LIMIT:.0f}, a person must approve"}
