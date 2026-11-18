"""Simple RAG: load .txt files -> chunk -> embed -> retrieve top-k -> ask the LLM."""
import os
import sys
import glob

import numpy as np
from sentence_transformers import SentenceTransformer
import anthropic

DOCS_DIR = os.path.join(os.path.dirname(__file__), "docs")
MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
CHUNK_WORDS = 120
OVERLAP = 20
TOP_K = 3

embedder = SentenceTransformer("all-MiniLM-L6-v2")


def load_chunks():
    """Read every .txt file and split into overlapping word chunks."""
    chunks = []
    for path in glob.glob(os.path.join(DOCS_DIR, "*.txt")):
        with open(path, encoding="utf-8") as f:
            words = f.read().split()
        step = CHUNK_WORDS - OVERLAP
        for i in range(0, max(len(words), 1), step):
            piece = " ".join(words[i : i + CHUNK_WORDS])
            if piece:
                chunks.append({"source": os.path.basename(path), "text": piece})
    return chunks


def build_index(chunks):
    vectors = embedder.encode([c["text"] for c in chunks], normalize_embeddings=True)
    return np.array(vectors)


def retrieve(question, chunks, vectors, k=TOP_K):
    q = embedder.encode([question], normalize_embeddings=True)[0]
    scores = vectors @ q  # cosine similarity (vectors are normalized)
    top = np.argsort(scores)[::-1][:k]
    return [chunks[i] for i in top]


def answer(question, context_chunks):
    context = "\n\n".join(f"[{c['source']}]\n{c['text']}" for c in context_chunks)
    prompt = (
        "Answer the question using only the context below. "
        "If the answer is not in the context, say you don't know.\n\n"
        f"Context:\n{context}\n\nQuestion: {question}"
    )
    client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY
    msg = client.messages.create(
        model=MODEL,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    return msg.content[0].text


def main():
    if not os.getenv("ANTHROPIC_API_KEY"):
        sys.exit("Set the ANTHROPIC_API_KEY environment variable first.")
    chunks = load_chunks()
    if not chunks:
        sys.exit("Add some .txt files to the docs/ folder first.")
    vectors = build_index(chunks)
    print(f"Indexed {len(chunks)} chunks. Ask a question (or 'quit').")

    while True:
        q = input("\n> ").strip()
        if q.lower() in {"quit", "exit", ""}:
            break
        top = retrieve(q, chunks, vectors)
        print("\nAnswer:", answer(q, top))
        print("Sources:", ", ".join(sorted({c["source"] for c in top})))


if __name__ == "__main__":
    main()
