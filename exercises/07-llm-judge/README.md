# Drill 7: An LLM judge you can trust

**Skill:** LLM-as-a-judge · **Time:** about 45 minutes

A support bot gets a new prompt. To decide if it's better than the old one, the team shows
both answers to an LLM judge and asks which one is better. It's fast and cheap, and the
results go straight into the release decision.

Nobody checked the judge. It has the habits real judge models have:

- **It likes long answers.** Without a reference answer it can't tell which answer is
  correct, so a long wrong answer beats a short right one.
- **It likes whatever it reads first.** When two answers are about equally good, it picks
  answer A. Swap them and it picks the other one.
- **It doesn't always follow the format.** It's asked to end with `[[A]]`, `[[B]]` or `[[C]]`
  (C means a tie), but it also writes things like `Verdict: B` or `**Winner: Answer A**`, and
  now and then it gives no verdict at all.

`judge.py` trusts every reply. It reads the verdict by checking if the letter "A" appears
anywhere in the text, it asks once, and it never passes the reference. Then the team "measured"
the judge by skipping every tie, so the number looked great.

## The judge model

`judge_model.py` simulates the judge LLM. Don't edit it: the checker uses its own copy.

```python
from judge_model import JudgeModel

model = JudgeModel()
reply = model.judge(question, answer_a, answer_b, reference=None)   # returns text
```

Every call costs money, so `model.calls` counts them.

## Your task

Fix the three functions in `judge.py`.

### 1. `parse_verdict(text)` returns `"A"`, `"B"`, `"tie"` or `None`

- If the reply has `[[A]]`, `[[B]]`, `[[C]]` or `[[tie]]` (any case, spaces allowed inside),
  use the **last** one. `[[C]]` means a tie.
- If there's no marker, look for `verdict`, `final verdict`, `winner` or `final answer`,
  then `:` or `-`, then the choice: `Verdict: B`, `winner: a`, `**Winner: Answer B**`,
  `**Final verdict:** A`. The choice can be A, B, "Answer A", "Answer B" or tie. Use the last one.
- "It's a tie" or "equally good" means a tie.
- Anything else is `None`. **Never guess.** "Answer A is wrong. Answer B is right." has no
  verdict in the format the judge was asked for, so it's `None`.

### 2. `judge_pair(model, question, answer_a, answer_b, reference=None)`

Return `{"winner": "A" | "B" | "tie", "confident": True | False}`.

1. **Give the judge the reference** whenever you have one. That's what lets it check facts
   instead of counting words.
2. **Ask in both orders:** once as `(answer_a, answer_b)` and once as `(answer_b, answer_a)`.
   Flip the second verdict back (its A is your B).
3. If a reply has **no verdict**, ask that same order **once more**. Never more than
   **4 calls** for one pair.
4. Both orders agree on A, B or tie: that's the winner, `confident: True`.
   Anything else (they disagree, or there's still no verdict): `"tie"`, `confident: False`.

### 3. `measure(judge, labeled, min_labels=20)`

`judge` is any function `judge(question, answer_a, answer_b, reference)` that returns a dict
with `"winner"`. `labeled` is a list of rows like the ones in `labeled.json`, each with a
human label in `"human"`.

Return `{"agreement": float, "n": int, "trusted": bool}`.

- **Count every row.** `n` is the number of rows. A tie is an answer: if the human said tie
  and the judge said tie, they agree. Don't skip anything.
- `agreement` is the number of matching rows divided by `n`, from 0 to 1. With no rows, it's
  `0.0` and `n` is 0.
- `trusted` is `True` only with **at least `min_labels` rows** and **agreement of 80% or more**.
  Twelve labels that all match isn't enough evidence.

`labeled.json` has 12 labeled pairs to try. The checker uses 30 hidden pairs: the judge has
to agree with the human labels at least **90%** of the time and **never pick the wrong answer**.

## Check your work

```bash
python3 -m drills check 7
```

Stuck? `python3 -m drills hint 7`
