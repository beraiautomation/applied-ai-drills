# Drill 2: Find the right part of the document

**Skill:** RAG retrieval · **Time:** about 45 minutes

A staff Q&A bot answers questions from `handbook.md`. Before the model answers, `rag.py`
finds the 3 most useful pieces of the handbook. The model can only be as good as those 3 pieces.

Right now the search is broken:

- `chunk()` cuts the text every 200 characters, often in the middle of a word or a fact.
- `retrieve()` only finds a chunk if it contains the whole question word for word.
  That almost never happens, so it returns the first 3 chunks every time.

## Your task

Fix the two functions in `rag.py`. Keep their names and what they return.

1. **`chunk(text)`** returns a list of `{"id": int, "section": str, "text": str}`.
   - Never cut a word in half. Each chunk is at most 800 characters.
   - Every part of the handbook must be in some chunk. Nothing gets lost.
   - `section` is the heading the chunk came from.
2. **`retrieve(chunks, question, k=3)`** returns the best `k` chunks, best first.
   - The right section should be in the top 3 for at least **85%** of questions.

No AI model or library needed. Plain Python is enough, and it must stay plain Python.

## Check your work

```bash
python3 -m drills check 2
```

The checker asks questions you haven't seen, about this handbook **and a second document**
you've never seen. So don't tune your code to the visible questions.
Stuck? `python3 -m drills hint 2`
