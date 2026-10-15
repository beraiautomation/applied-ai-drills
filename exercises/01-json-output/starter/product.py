"""Turn a product description into clean data, using a language model."""
import json

PROMPT = """Extract the product from this text. Reply with JSON only, using these keys:
name (text), price (number), currency (3-letter code like USD), in_stock (true or false).

Text: {text}"""


def get_product(text, call_model):
    """Return {"name": str, "price": float, "currency": str, "in_stock": bool}.

    call_model(prompt) sends a prompt to the model and returns its reply as a string.
    """
    reply = call_model(PROMPT.format(text=text))
    return json.loads(reply)
