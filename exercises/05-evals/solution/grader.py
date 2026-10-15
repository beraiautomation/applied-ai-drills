"""Decide if a support bot's answer is correct, compared to a reference answer."""
import re

WORDS = {"zero": 0, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
         "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12, "fifteen": 15, "twenty": 20,
         "thirty": 30, "forty": 40, "fifty": 50, "hundred": 100}
NON_ANSWER = re.compile(r"\b(i don'?t know|not sure|no idea|can'?t help|cannot help|contact (support|the store|us)|"
                        r"unable to (answer|help)|i can'?t find)\b", re.I)
NEGATION = re.compile(r"\b(no|not|can'?t|cannot|won'?t|isn'?t|aren'?t|doesn'?t|don'?t|never|only)\b", re.I)
STOP = set("""a an and are as at be by can do does for from get has have i if in is it its of on or our
the their there they this to was we what when where which who will with you your it's that only""".split())


def numbers(text):
    """All numbers in the text, normalized: '$1,450.00' -> '1450', '6pm' -> '18:00', 'two' -> '2'."""
    text = text.lower()
    found = set()

    def clock(hour, minute, ampm=None):
        hour, minute = int(hour), int(minute or 0)
        if ampm == "pm" and hour < 12:
            hour += 12
        if ampm == "am" and hour == 12:
            hour = 0
        found.add(f"{hour}:{minute:02d}")
        return " "

    text = re.sub(r"\b(\d{1,2})(?::(\d{2}))?\s*(am|pm)\b", lambda m: clock(*m.groups()), text)
    text = re.sub(r"\b(\d{1,2}):(\d{2})\b", lambda m: clock(*m.groups()), text)
    # Skip numbers that are part of a name or code, like "E2" or "4B".
    for raw in re.findall(r"(?<![a-z\d])\d[\d,]*(?:\.\d+)?(?![a-z\d])", text):
        value = float(raw.replace(",", ""))
        found.add(str(int(value)) if value == int(value) else f"{value:g}")
    for tens, ones in re.findall(r"\b(twenty|thirty|forty|fifty)-(one|two|three|four|five|six|seven|eight|nine)\b", text):
        found.add(str(WORDS[tens] + WORDS[ones]))
    text = re.sub(r"\b(twenty|thirty|forty|fifty)-(one|two|three|four|five|six|seven|eight|nine)\b", " ", text)
    for word in re.findall(r"[a-z]+", text):
        if word in WORDS:
            found.add(str(WORDS[word]))
    return found


def _polarity(text):
    first = re.findall(r"[a-z']+", text.lower())[:1]
    if first == ["yes"]:
        return True
    if first == ["no"]:
        return False
    return None


def _keywords(text):
    return {w.rstrip("s") for w in re.findall(r"[a-z]+", text.lower()) if w not in STOP and len(w) > 2}


def grade(question, reference, answer):
    """Return True if the answer is correct, False if not."""
    if not answer.strip() or NON_ANSWER.search(answer):
        return False
    ref_nums, ans_nums, q_nums = numbers(reference), numbers(answer), numbers(question)
    if not ref_nums <= ans_nums:          # a fact is missing or different
        return False
    if not ans_nums <= ref_nums | q_nums:  # a made-up number
        return False
    ref_yes, ans_yes = _polarity(reference), _polarity(answer)
    if ref_yes is not None:
        if ans_yes is not None:
            return ans_yes == ref_yes
        return bool(NEGATION.search(answer)) == (not ref_yes)
    if ref_nums:
        return True
    ref_words = _keywords(reference) - _keywords(question)
    if not ref_words:
        return True
    return len(ref_words & _keywords(answer)) / len(ref_words) >= 0.5
