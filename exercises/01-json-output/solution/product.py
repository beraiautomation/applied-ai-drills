"""Turn a product description into clean data, using a language model."""
import json
import re

PROMPT = """Extract the product from this text. Reply with JSON only, using these keys:
name (text), price (number), currency (3-letter code like USD), in_stock (true or false).

Text: {text}"""

RETRY = PROMPT + "\n\nYour last reply had a problem: {error}. Reply again with valid JSON only."
KEYS = ("name", "price", "currency", "in_stock")
MAX_CALLS = 3


def _extract(reply):
    """Find the JSON object in a reply, even with fences or chatter around it."""
    start, end = reply.find("{"), reply.rfind("}")
    if start == -1 or end <= start:
        raise ValueError("the reply was not valid JSON (no object found)")
    raw = re.sub(r",\s*([}\]])", r"\1", reply[start:end + 1])  # trailing commas
    try:
        data = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise ValueError(f"the reply was not valid JSON ({exc.msg})") from None
    if not isinstance(data, dict):
        raise ValueError("the reply was not a JSON object")
    return data


def _price(value):
    if isinstance(value, bool):
        raise ValueError("price must be a number")
    if isinstance(value, str):
        value = value.strip().replace("$", "").replace("€", "").replace("£", "").replace(",", "")
    try:
        price = float(value)
    except (TypeError, ValueError):
        raise ValueError("price must be a number") from None
    if price <= 0:
        raise ValueError("price must be above 0")
    return price


def _in_stock(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str) and value.strip().lower() in ("true", "yes"):
        return True
    if isinstance(value, str) and value.strip().lower() in ("false", "no"):
        return False
    raise ValueError("in_stock must be true or false")


def _validate(data):
    missing = [k for k in KEYS if k not in data]
    if missing:
        raise ValueError("missing key: " + ", ".join(missing))
    name = data["name"].strip() if isinstance(data["name"], str) else ""
    if not name:
        raise ValueError("name must be non-empty text")
    currency = data["currency"].strip().upper() if isinstance(data["currency"], str) else ""
    if not re.fullmatch(r"[A-Z]{3}", currency):
        raise ValueError("currency must be a 3-letter code like USD")
    return {"name": name, "price": _price(data["price"]), "currency": currency,
            "in_stock": _in_stock(data["in_stock"])}


def get_product(text, call_model):
    """Return {"name": str, "price": float, "currency": str, "in_stock": bool}."""
    prompt = PROMPT.format(text=text)
    error = None
    for _ in range(MAX_CALLS):
        reply = call_model(prompt)
        try:
            return _validate(_extract(reply))
        except ValueError as exc:
            error = str(exc)
            prompt = RETRY.format(text=text, error=error)
    raise ValueError(f"no valid reply after {MAX_CALLS} tries: {error}")
