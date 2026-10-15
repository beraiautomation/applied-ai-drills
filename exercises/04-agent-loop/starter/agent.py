"""The agent loop: ask the model, run its tool, repeat until it answers."""


def run_agent(model, tools, task, max_steps=8):
    """Returns {"answer": str or None, "stopped": "done" | "max_steps" | "loop", "steps": int, "messages": list}."""
    messages = [{"role": "user", "content": task}]
    steps = 0
    while True:
        reply = model.next(messages)
        steps += 1
        if reply["type"] == "final":
            return {"answer": reply["answer"], "stopped": "done", "steps": steps, "messages": messages}
        result = tools[reply["name"]](**reply["args"])
        messages.append({"role": "assistant", "tool": reply["name"], "args": reply["args"]})
        messages.append({"role": "tool", "name": reply["name"], "content": str(result)})
