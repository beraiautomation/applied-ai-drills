# Drill 5: An eval that catches wrong answers

**Skill:** evals · **Time:** about 45 minutes

A support bot answers customer questions. Before each release, an eval checks its answers
against reference answers. `grader.py` decides if an answer is correct.

Today it only accepts answers that match the reference word for word, so it fails good
answers like "It's $45." for the reference "A basic service costs 45 pounds." Teams then stop
trusting the eval and turn it off. That's how bugs reach customers.

## Your task

Fix `grade(question, reference, answer)` in `grader.py` to return `True` when the answer is
correct and `False` when it isn't.

**Correct** means the answer has the same facts as the reference, even in different words:
- `"$1,450"`, `"1450 dollars"` and `"1,450.00"` are the same number.
- `"two"` and `"2"`, and `"20%"` and `"20 percent"`, are the same.
- `"6pm"` and `"18:00"` are the same time.

**Wrong** means any of these:
- A number is different, or a number from the reference is missing.
- The answer **adds a number** that isn't in the reference or the question. That's a made-up detail.
- It says the opposite (no instead of yes).
- It doesn't answer ("I don't know", "please contact support").

No AI model allowed: the grader must give the same result every time.

`cases.json` has 12 labeled examples to try. The checker uses about 40 hidden ones and needs
**90% right and zero made-up answers accepted**. A grader that lets a made-up number through is
worse than no grader.

## Check your work

```bash
python3 -m drills check 5
```

Stuck? `python3 -m drills hint 5`
