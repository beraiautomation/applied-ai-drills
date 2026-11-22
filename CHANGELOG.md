# Changelog

## 0.2.0

- New drill 7, **An LLM judge you can trust**: read messy judge verdicts, give the judge the
  reference, ask in both orders to cancel position bias, retry when there's no verdict, and
  measure the judge against human labels before trusting it.
- The simulated judge model has the habits real judges have: it prefers long answers, prefers
  whatever it reads first, and doesn't always follow the output format.
- CI checks new shortcuts for drill 7: a judge that always says tie, a judge without the
  reference, a measure that always trusts, and an edited judge model.

## 0.1.0

- Six drills: structured output, RAG retrieval, tool calling, agent loop, evals and guardrails.
- Hidden test cases, cheat checks and a selftest that proves every grader.
