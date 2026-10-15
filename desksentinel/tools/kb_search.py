"""Tiny RAG index over security knowledge sources.

Embeds *.md / *.txt files from data/kb/ with a sentence-transformer,
then returns the top-k chunks per query so the agent's verdicts cite
real indicators (e.g. CISA phishing guidance) instead of vibes.
"""
from __future__ import annotations

import math
from pathlib import Path

DEFAULT_KB_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "kb"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a)) or 1e-9
    nb = math.sqrt(sum(y * y for y in b)) or 1e-9
    return dot / (na * nb)


class KBSearch:
    def __init__(self, kb_dir: str | Path = DEFAULT_KB_DIR, model_name: str = MODEL_NAME):
        from sentence_transformers import SentenceTransformer

        self.model = SentenceTransformer(model_name)
        self.chunks: list[tuple[str, str]] = []  # (source, text)
        kb_dir = Path(kb_dir)
        for f in sorted(kb_dir.glob("*")):
            if f.suffix.lower() in {".md", ".txt"}:
                text = f.read_text(encoding="utf-8", errors="ignore")
                # chunk on blank lines, drop tiny fragments
                for chunk in text.split("\n\n"):
                    chunk = chunk.strip()
                    if len(chunk) > 80:
                        self.chunks.append((f.name, chunk))
        self.embeddings = self.model.encode(
            [c for _, c in self.chunks], convert_to_numpy=False
        ).tolist()

    def search(self, query: str, top_k: int = 3) -> list[dict]:
        """Return top_k {source, text, score} chunks for the query."""
        q = self.model.encode([query], convert_to_numpy=False).tolist()[0]
        scored = [
            (src, txt, _cosine(q, emb))
            for (src, txt), emb in zip(self.chunks, self.embeddings)
        ]
        scored.sort(key=lambda t: t[2], reverse=True)
        return [
            {"source": src, "text": txt, "score": round(s, 3)}
            for src, txt, s in scored[:top_k]
        ]


if __name__ == "__main__":
    kb = KBSearch()
    for hit in kb.search("what are common phishing indicators"):
        print(hit["source"], hit["score"])
        print(hit["text"][:200], "\n---")
