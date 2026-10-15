"""Decide if a support bot's answer is correct, compared to a reference answer."""


def grade(question, reference, answer):
    """Return True if the answer is correct, False if not."""
    return answer.strip().lower() == reference.strip().lower()
