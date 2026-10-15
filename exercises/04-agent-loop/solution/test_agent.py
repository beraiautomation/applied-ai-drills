"""A few visible tests. Run: python3 test_agent.py"""
from agent import run_agent


class Script:
    """A pretend model that replies from a list. It stops the test if called too often."""

    def __init__(self, *replies):
        self.replies, self.calls = list(replies), 0

    def next(self, messages):
        self.calls += 1
        if self.calls > 30:
            raise RuntimeError("model called more than 30 times: the loop never stops")
        return self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]


TOOLS = {"get_weather": lambda city: f"Sunny in {city}"}


def test_simple():
    m = Script({"type": "tool", "name": "get_weather", "args": {"city": "Leeds"}},
               {"type": "final", "answer": "It's sunny."})
    r = run_agent(m, TOOLS, "Weather in Leeds?")
    assert r["stopped"] == "done" and r["answer"] == "It's sunny." and r["steps"] == 2


def test_step_limit():
    m = Script({"type": "tool", "name": "get_weather", "args": {"city": "Leeds"}},
               {"type": "tool", "name": "get_weather", "args": {"city": "York"}},
               {"type": "tool", "name": "get_weather", "args": {"city": "Hull"}},
               {"type": "tool", "name": "get_weather", "args": {"city": "Bath"}})
    r = run_agent(m, TOOLS, "Weather everywhere?", max_steps=4)
    assert r["stopped"] == "max_steps" and r["answer"] is None and m.calls == 4


def test_tool_error():
    m = Script({"type": "tool", "name": "get_weather", "args": {}},
               {"type": "final", "answer": "Sorry, I couldn't check."})
    r = run_agent(m, TOOLS, "Weather?")
    assert r["stopped"] == "done" and r["messages"][-1]["content"].startswith("error:")


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
