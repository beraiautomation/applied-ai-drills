"""The agent loop: ask the model, run its tool, repeat until it answers."""
import json
from collections import Counter

MAX_SAME_CALL = 2


def run_agent(model, tools, task, max_steps=8):
    """Returns {"answer": str or None, "stopped": "done" | "max_steps" | "loop", "steps": int, "messages": list}."""
    messages = [{"role": "user", "content": task}]
    seen = Counter()
    for step in range(1, max_steps + 1):
        reply = model.next(messages)
        if reply.get("type") == "final":
            return {"answer": reply.get("answer"), "stopped": "done", "steps": step, "messages": messages}

        name, args = reply.get("name"), reply.get("args") or {}
        key = (name, json.dumps(args, sort_keys=True, default=str))
        if seen[key] >= MAX_SAME_CALL:
            return {"answer": None, "stopped": "loop", "steps": step, "messages": messages}
        seen[key] += 1

        messages.append({"role": "assistant", "tool": name, "args": args})
        if name not in tools:
            content = f"error: unknown tool {name}. Available tools: {', '.join(tools)}"
        else:
            try:
                content = str(tools[name](**args))
            except Exception as exc:  # noqa: BLE001 - the model should see the error and recover
                content = f"error: {type(exc).__name__}: {exc}"
        messages.append({"role": "tool", "name": name, "content": content})

    return {"answer": None, "stopped": "max_steps", "steps": max_steps, "messages": messages}
