# RAG Question Answering

Pipeline: load `docs/*.txt` -> split into overlapping chunks -> embed with
sentence-transformers -> cosine-similarity retrieval -> LLM answers from the retrieved context.

```
pip install -r requirements.txt
export ANTHROPIC_API_KEY=your_key      # Windows: set ANTHROPIC_API_KEY=your_key
python rag.py
```
Add your own `.txt` files to `docs/` and ask questions about them.
