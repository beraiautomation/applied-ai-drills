"""Find the parts of a document that answer a question (the "R" in RAG)."""
import math
import re

MAX_CHARS = 800
STOP = set("""a an and are as at be by can do does for from get gets how i if in is it its of on or
should the their there they this to was we what when where which who why will with you your our my
me much many long""".split())


def _sentences(text):
    return [s for s in re.split(r"(?<=[.!?])\s+", text.strip()) if s]


def chunk(text):
    """Split a document into chunks: a list of {"id": int, "section": str, "text": str}."""
    chunks = []
    section, lines = "", []

    def flush():
        body = " ".join(" ".join(lines).split())
        if not body:
            return
        piece = ""
        for sentence in _sentences(body):
            while len(sentence) > MAX_CHARS:  # a giant sentence: split at the last space
                cut = sentence.rfind(" ", 0, MAX_CHARS)
                cut = cut if cut > 0 else MAX_CHARS
                if piece:
                    chunks.append({"id": len(chunks), "section": section, "text": piece})
                    piece = ""
                chunks.append({"id": len(chunks), "section": section, "text": sentence[:cut]})
                sentence = sentence[cut:].strip()
            if piece and len(piece) + 1 + len(sentence) > MAX_CHARS:
                chunks.append({"id": len(chunks), "section": section, "text": piece})
                piece = sentence
            else:
                piece = f"{piece} {sentence}".strip()
        if piece:
            chunks.append({"id": len(chunks), "section": section, "text": piece})

    for line in text.splitlines():
        m = re.match(r"^#{1,6}\s+(.*)", line)
        if m:
            flush()
            section, lines = m.group(1).strip(), []
        else:
            lines.append(line)
    flush()
    return chunks


def _stem(word):
    for suffix in ("ing", "ed", "es", "s"):
        if word.endswith(suffix) and len(word) - len(suffix) >= 3:
            return word[: -len(suffix)]
    return word


def _terms(text):
    return [_stem(w) for w in re.findall(r"[a-z0-9]+", text.lower()) if w not in STOP]


def retrieve(chunks, question, k=3):
    """BM25 ranking over the section title and the text."""
    docs = [_terms(c["section"] + " " + c["section"] + " " + c["text"]) for c in chunks]
    n = len(docs)
    avg = sum(len(d) for d in docs) / max(n, 1)
    df = {}
    for d in docs:
        for t in set(d):
            df[t] = df.get(t, 0) + 1
    query = _terms(question)
    k1, b = 1.5, 0.75
    scored = []
    for c, d in zip(chunks, docs):
        score = 0.0
        for t in query:
            tf = d.count(t)
            if tf:
                idf = math.log(1 + (n - df[t] + 0.5) / (df[t] + 0.5))
                score += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * len(d) / avg))
        scored.append((score, -c["id"], c))
    scored.sort(key=lambda s: (s[0], s[1]), reverse=True)
    return [c for _, _, c in scored[:k]]
