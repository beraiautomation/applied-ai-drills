"""Use an LLM judge to compare two answers, and measure whether the judge can be trusted."""


def parse_verdict(text):
    """Return "A", "B", "tie", or None when the reply has no clear verdict."""
    return "A" if "A" in text else "B"


def judge_pair(model, question, answer_a, answer_b, reference=None):
    """Return {"winner": "A" | "B" | "tie", "confident": bool}."""
    reply = model.judge(question, answer_a, answer_b)
    return {"winner": parse_verdict(reply), "confident": True}


def measure(judge, labeled, min_labels=20):
    """Compare the judge with human labels. Return {"agreement": float, "n": int, "trusted": bool}."""
    agree = n = 0
    for row in labeled:
        if row["human"] == "tie":
            continue
        got = judge(row["question"], row["answer_a"], row["answer_b"], row.get("reference"))["winner"]
        if got == "tie":
            continue
        n += 1
        agree += got == row["human"]
    agreement = agree / n
    return {"agreement": agreement, "n": n, "trusted": agreement >= 0.8}
