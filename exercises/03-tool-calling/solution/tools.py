"""Tools a support agent can call, and the code that runs them."""
import json
import re

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


def _coerce(field, spec, value):
    """Return (value, error)."""
    if spec["type"] == "string":
        if not isinstance(value, str):
            return None, f"{field} must be text"
        if "pattern" in spec and not re.fullmatch(spec["pattern"], value):
            return None, f"{field} has the wrong format: {value!r}"
        if "enum" in spec and value not in spec["enum"]:
            return None, f"{field} must be one of {', '.join(spec['enum'])}"
        return value, None
    if spec["type"] == "number":
        if isinstance(value, bool):
            return None, f"{field} must be a number"
        if isinstance(value, str):
            try:
                value = float(value.strip())
            except ValueError:
                return None, f"{field} must be a number"
        if not isinstance(value, (int, float)) or value != value:
            return None, f"{field} must be a number"
        if "min_exclusive" in spec and value <= spec["min_exclusive"]:
            return None, f"{field} must be a number above {spec['min_exclusive']}"
        return float(value), None
    return None, f"{field} has an unknown type"


def execute(call):
    """Run one tool call from the model. Returns {"ok": True, "result": ...} or {"ok": False, "error": ...}."""
    try:
        name = call.get("name") if isinstance(call, dict) else None
        if name not in TOOLS:
            return {"ok": False, "error": f"unknown tool: {name}. Available: {', '.join(TOOLS)}"}
        raw = call.get("arguments") or "{}"
        try:
            args = json.loads(raw) if isinstance(raw, str) else raw
        except json.JSONDecodeError:
            return {"ok": False, "error": "arguments are not valid JSON"}
        if not isinstance(args, dict):
            return {"ok": False, "error": "arguments must be a JSON object"}
        schema = TOOLS[name]
        allowed = {**schema["required"], **schema["optional"]}
        extra = [k for k in args if k not in allowed]
        if extra:
            return {"ok": False, "error": f"unknown argument: {extra[0]}"}
        clean = {}
        for field, spec in allowed.items():
            if field not in args:
                if field in schema["required"]:
                    return {"ok": False, "error": f"missing required argument: {field}"}
                continue
            value, error = _coerce(field, spec, args[field])
            if error:
                return {"ok": False, "error": error}
            clean[field] = value
        if "order_id" in clean and clean["order_id"] not in ORDERS:
            return {"ok": False, "error": f"order_id not found: {clean['order_id']}"}
        if name == "refund" and clean["amount"] > ORDERS[clean["order_id"]]["total"]:
            total = ORDERS[clean["order_id"]]["total"]
            return {"ok": False, "error": f"amount {clean['amount']:.2f} is more than the order total {total:.2f}"}
        return {"ok": True, "result": FUNCTIONS[name](**clean)}
    except Exception as exc:  # noqa: BLE001 - never crash the agent
        return {"ok": False, "error": f"tool failed: {type(exc).__name__}"}
