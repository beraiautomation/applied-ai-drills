"""Tools a support agent can call, and the code that runs them."""
import json

ORDERS = {
    "ORD-1042": {"customer": "Maria Lopez", "total": 89.50, "status": "delivered"},
    "ORD-1043": {"customer": "James Chen", "total": 25.00, "status": "shipped"},
    "ORD-1044": {"customer": "Grace Obi", "total": 1200.00, "status": "delivered"},
}
RATES = {("USD", "EUR"): 0.92, ("EUR", "USD"): 1.09, ("USD", "GBP"): 0.79,
         ("GBP", "USD"): 1.27, ("EUR", "GBP"): 0.86, ("GBP", "EUR"): 1.16}

TOOLS = {
    "get_order": {
        "required": {"order_id": {"type": "string", "pattern": r"^ORD-\d{4}$"}},
        "optional": {},
    },
    "refund": {
        "required": {"order_id": {"type": "string", "pattern": r"^ORD-\d{4}$"},
                     "amount": {"type": "number", "min_exclusive": 0}},
        "optional": {"reason": {"type": "string"}},
    },
    "convert_currency": {
        "required": {"amount": {"type": "number", "min_exclusive": 0},
                     "from_currency": {"type": "string", "enum": ["USD", "EUR", "GBP"]},
                     "to_currency": {"type": "string", "enum": ["USD", "EUR", "GBP"]}},
        "optional": {},
    },
}


def get_order(order_id):
    return {"order_id": order_id, **ORDERS[order_id]}


def refund(order_id, amount, reason=""):
    return {"order_id": order_id, "refunded": round(amount, 2), "reason": reason}


def convert_currency(amount, from_currency, to_currency):
    if from_currency == to_currency:
        return {"amount": round(amount, 2), "currency": to_currency}
    return {"amount": round(amount * RATES[(from_currency, to_currency)], 2), "currency": to_currency}


FUNCTIONS = {"get_order": get_order, "refund": refund, "convert_currency": convert_currency}


def execute(call):
    """Run one tool call from the model. Returns {"ok": True, "result": ...} or {"ok": False, "error": ...}."""
    args = json.loads(call["arguments"])
    result = FUNCTIONS[call["name"]](**args)
    return {"ok": True, "result": result}
