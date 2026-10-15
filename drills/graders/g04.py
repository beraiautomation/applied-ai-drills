"""Grader for drill 4: an agent loop that knows when to stop."""
from __future__ import annotations

from pathlib import Path

from .common import Check, load, score_cases, unchanged, visible_tests


class Script:
    def __init__(self, *replies):
        self.replies, self.calls, self.seen = list(replies), 0, []

    def next(self, messages):
        self.calls += 1
        self.seen.append([dict(m) for m in messages])
        if self.calls > 40:
            raise RuntimeError("model called more than 40 times: the loop never stops")
        return self.replies.pop(0) if len(self.replies) > 1 else self.replies[0]


def tool(name, **args):
    return {"type": "tool", "name": name, "args": args}


def final(text):
    return {"type": "final", "answer": text}


class Tools(dict):
    def __init__(self):
        self.runs = []
        super().__init__(
            lookup=self._wrap("lookup", lambda q: f"result for {q}"),
            fail=self._wrap("fail", self._fail),
            add=self._wrap("add", lambda a, b: a + b),
        )

    def _wrap(self, name, fn):
        def run(**kw):
            self.runs.append(name)
            return fn(**kw)
        return run

    @staticmethod
    def _fail(**kw):
        raise ConnectionError("database timeout")


def grade(folder: Path, original: Path) -> list:
    checks = [unchanged(folder, original, "test_agent.py"), visible_tests(folder, "test_agent.py")]
    try:
        run_agent = load(folder, "agent").run_agent
    except Exception as exc:  # noqa: BLE001
        return checks + [Check("agent.py loads", False, str(exc)[:150])]

    def scenario(case):
        replies, kwargs, test = case
        m, t = Script(*replies), Tools()
        r = run_agent(m, t, "help me", **kwargs)
        return test(r, m, t)

    def expect(stopped, steps=None, answer=..., extra=None):
        def test(r, m, t):
            if r.get("stopped") != stopped:
                return f'stopped="{r.get("stopped")}", want "{stopped}"'
            if steps is not None and (r.get("steps") != steps or m.calls != steps):
                return f"steps={r.get('steps')} and model calls={m.calls}, want {steps}"
            if answer is not ... and r.get("answer") != answer:
                return f"answer={r.get('answer')!r}, want {answer!r}"
            return extra(r, m, t) if extra else None
        return test

    def result_reaches_model(r, m, t):
        last_seen = m.seen[-1]
        if not any(x.get("role") == "tool" and "result for orders" in str(x.get("content")) for x in last_seen):
            return "the model never saw the tool result"
        if last_seen[0] != {"role": "user", "content": "help me"}:
            return "the first message should be the user's task"
        return None

    def ran_twice(r, m, t):
        return None if t.runs.count("lookup") == 2 else f"the repeated tool ran {t.runs.count('lookup')} times, want 2"

    def error_shown(r, m, t):
        msgs = [x for x in m.seen[-1] if x.get("role") == "tool"]
        if not msgs or not str(msgs[-1].get("content", "")).startswith("error:"):
            return "no 'error:' tool message reached the model"
        return None

    def names_tool(r, m, t):
        msgs = [x for x in m.seen[-1] if x.get("role") == "tool"]
        if not msgs or "send_email" not in str(msgs[-1].get("content", "")):
            return "the error doesn't name the unknown tool"
        return error_shown(r, m, t)

    endless = [tool("lookup", q=f"page {i}") for i in range(20)]
    cases = [
        ("tool, then answer", ([tool("lookup", q="orders"), final("Found it.")], {}, expect("done", 2, "Found it.", result_reaches_model))),
        ("answers right away", ([final("Hi!")], {}, expect("done", 1, "Hi!"))),
        ("same call forever", ([tool("lookup", q="x")], {}, expect("loop", 3, None, ran_twice))),
        ("same call, args in a different order", ([tool("add", a=1, b=2), tool("add", b=2, a=1), tool("add", a=1, b=2), final("3")], {}, expect("loop", 3))),
        ("A, B, A, B, A", ([tool("lookup", q="a"), tool("lookup", q="b"), tool("lookup", q="a"), tool("lookup", q="b"), tool("lookup", q="a"), final("x")], {}, expect("loop", 5))),
        ("never finishes", (endless, {}, expect("max_steps", 8, None))),
        ("never finishes, max_steps=3", (endless, {"max_steps": 3}, expect("max_steps", 3, None))),
        ("tool raises, then recovers", ([tool("fail"), final("Sorry, the system is down.")], {}, expect("done", 2, "Sorry, the system is down.", error_shown))),
        ("unknown tool, then recovers", ([tool("send_email", to="x"), final("I can't send email.")], {}, expect("done", 2, "I can't send email.", names_tool))),
        ("wrong arguments, then recovers", ([tool("add", a=1), tool("add", a=1, b=2), final("3")], {}, expect("done", 3, "3", None))),
    ]
    checks.append(score_cases("stops, recovers and never runs away", cases, scenario))
    return checks
