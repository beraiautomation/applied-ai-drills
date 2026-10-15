# Drill 1: Clean JSON from a messy model

**Skill:** structured output · **Time:** about 30 minutes

Your shop uses a language model to turn product descriptions into data. The code in
`product.py` trusts the model completely. In real use, the model:

- wraps the JSON in ```` ```json ```` fences, or adds a sentence before or after it
- writes `"price": "$12.50"` instead of a number, or `"currency": "usd"`
- leaves a trailing comma, like `{"name": "Mug",}`
- sometimes forgets a key, or replies with no JSON at all

Each of these crashes the app today.

## Your task

Fix `get_product(text, call_model)` in `product.py` so it always returns exactly:

```python
{"name": str, "price": float, "currency": str, "in_stock": bool}
```

1. **Find the JSON** even with fences or words around it, and fix trailing commas.
2. **Check every key.** `name` is non-empty text (trim spaces). `price` is a number above 0.
   `currency` is 3 capital letters. `in_stock` is true or false. No other keys in the result.
3. **Small fixes are OK.** `"$12.50"` or `"12.50"` becomes `12.5`. `"usd"` becomes `"USD"`.
   `"true"`, `"false"`, `"yes"`, `"no"` become booleans.
4. **Ask again when it can't be fixed.** Call the model again with a prompt that has the
   original text **and names the problem**: the missing or bad key, or that the reply wasn't valid JSON.
5. **At most 3 calls in total.** After 3 bad replies, raise `ValueError`.

`call_model(prompt)` returns the model's reply as a string. You can't change the model, only your code.

## Check your work

```bash
python3 -m drills check 1
```

The visible tests in `test_product.py` are a start. The checker also runs hidden cases.
Stuck? `python3 -m drills hint 1`
