"""A few visible tests. Run: python3 test_product.py"""
from product import get_product


def model_that_says(*replies):
    replies = list(replies)
    return lambda prompt: replies.pop(0)


def test_plain_json():
    m = model_that_says('{"name": "Blue Mug", "price": 12.5, "currency": "USD", "in_stock": true}')
    assert get_product("A blue mug, $12.50, in stock", m) == {
        "name": "Blue Mug", "price": 12.5, "currency": "USD", "in_stock": True}


def test_fenced_json():
    m = model_that_says('Here you go:\n```json\n{"name": "Lamp", "price": 40, "currency": "EUR", "in_stock": false}\n```')
    assert get_product("Lamp, 40 euros, sold out", m)["price"] == 40.0


def test_price_as_text():
    m = model_that_says('{"name": "Pen", "price": "$2.25", "currency": "usd", "in_stock": "yes"}')
    assert get_product("Pen for $2.25", m) == {"name": "Pen", "price": 2.25, "currency": "USD", "in_stock": True}


if __name__ == "__main__":
    passed = 0
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            try:
                fn()
                print("PASS", name)
                passed += 1
            except Exception as exc:  # noqa: BLE001
                print("FAIL", name, "-", type(exc).__name__, exc)
    print(f"{passed} of 3 visible tests passed")
