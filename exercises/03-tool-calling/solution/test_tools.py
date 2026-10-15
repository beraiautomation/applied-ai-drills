"""A few visible tests. Run: python3 test_tools.py"""
import json

from tools import execute


def call(name, **args):
    return {"name": name, "arguments": json.dumps(args)}


def test_good_call():
    r = execute(call("get_order", order_id="ORD-1042"))
    assert r["ok"] and r["result"]["total"] == 89.50


def test_unknown_tool():
    r = execute(call("delete_everything"))
    assert r["ok"] is False and "delete_everything" in r["error"]


def test_refund_too_big():
    r = execute(call("refund", order_id="ORD-1043", amount=500))
    assert r["ok"] is False and "amount" in r["error"]


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
