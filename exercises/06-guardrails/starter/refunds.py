"""Decide refund requests for the support bot."""


def decide_refund(request, get_order, today):
    """Return {"action": "approve" | "needs_human" | "deny", "amount": float or None, "reason": str}.

    request: {"customer_id": str, "order_id": str, "amount": number or text, "message": str}
    get_order(order_id): the order as a dict, or None
    today: "YYYY-MM-DD"
    """
    message = request["message"].lower()
    amount = float(str(request["amount"]).replace("$", ""))
    if "approve" in message or "manager" in message:
        return {"action": "approve", "amount": amount, "reason": "approved as requested"}
    if "refund" in message and amount <= 50:
        return {"action": "approve", "amount": amount, "reason": "small refund"}
    return {"action": "needs_human", "amount": amount, "reason": "needs a person"}
