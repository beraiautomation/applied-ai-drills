# Drill 4: An agent that knows when to stop

**Skill:** agent loop · **Time:** about 40 minutes

`run_agent()` in `agent.py` is the loop at the heart of every agent: ask the model what to
do, run the tool it picks, show it the result, and repeat until it gives an answer.

The loop in `agent.py` has no limits. If the model keeps asking for the same tool, it runs
forever and burns money. If a tool throws an error, the whole agent crashes.

The model talks like this. `model.next(messages)` returns either:

```python
{"type": "tool", "name": "search_orders", "args": {"email": "maria@gmail.com"}}
{"type": "final", "answer": "Your order ships tomorrow."}
```

## Your task

Fix `run_agent(model, tools, task, max_steps=8)` so it returns
`{"answer": ..., "stopped": ..., "steps": ..., "messages": [...]}`.

1. **Done:** when the model gives a final answer, stop with `stopped = "done"`.
2. **Step limit:** never call `model.next()` more than `max_steps` times. If it runs out,
   stop with `stopped = "max_steps"` and `answer = None`.
3. **Loop detection:** if the model asks for the **exact same tool call** (same name and same
   args) that already ran twice, don't run it again. Stop with `stopped = "loop"`.
4. **Tool errors:** if a tool raises, don't crash. Add a tool message whose content starts
   with `error:` and let the model try again.
5. **Unknown tools:** same, an `error:` message that names the tool.
6. `steps` is how many times you called `model.next()`.

Message formats (the model reads these):

```python
{"role": "user", "content": task}                              # first message
{"role": "assistant", "tool": name, "args": args}              # each tool call
{"role": "tool", "name": name, "content": "result or error: ..."}
```

## Check your work

```bash
python3 -m drills check 4
```

Stuck? `python3 -m drills hint 4`
