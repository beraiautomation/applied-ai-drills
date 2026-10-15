# Drill 3: Safe tool calls

**Skill:** tool calling · **Time:** about 40 minutes

A support agent can call three tools: `get_order`, `refund` and `convert_currency`.
The model sends a tool call like this:

```python
{"name": "refund", "arguments": "{\"order_id\": \"ORD-1042\", \"amount\": 25}"}
```

`execute(call)` in `tools.py` runs it. Today it trusts the model, so a bad call crashes the
app, or worse, refunds more than the customer paid.

## Your task

Fix `execute(call)` so it **never raises** and always returns one of:

```python
{"ok": True, "result": ...}
{"ok": False, "error": "a short message that names the problem field"}
```

1. **Bad JSON** in `arguments`: error, don't crash.
2. **Unknown tool**: error.
3. **Check every argument** against the schemas in `TOOLS`: required fields, no unknown
   extra fields, types, `pattern` and `enum`. Each error must **name the field**, so the model can fix it.
4. **Numbers may arrive as text**, like `"25.50"`. Accept that, but reject `true`, `"abc"`,
   and amounts of 0 or less.
5. **Business rule:** a refund can't be more than the order total, and the order must exist.

Why it matters: the error message goes back to the model. A clear message ("amount must be
a number above 0") lets it fix the call on the next try. A crash ends the conversation.

## Check your work

```bash
python3 -m drills check 3
```

Stuck? `python3 -m drills hint 3`
