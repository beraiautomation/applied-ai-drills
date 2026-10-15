"""Find the parts of a document that answer a question (the "R" in RAG)."""


def chunk(text):
    """Split a document into chunks: a list of {"id": int, "section": str, "text": str}."""
    size = 200
    chunks = []
    for i in range(0, len(text), size):
        chunks.append({"id": len(chunks), "section": "", "text": text[i:i + size]})
    return chunks


def retrieve(chunks, question, k=3):
    """Return the k chunks most likely to answer the question, best first."""
    hits = [c for c in chunks if question.lower() in c["text"].lower()]
    return (hits + [c for c in chunks if c not in hits])[:k]
