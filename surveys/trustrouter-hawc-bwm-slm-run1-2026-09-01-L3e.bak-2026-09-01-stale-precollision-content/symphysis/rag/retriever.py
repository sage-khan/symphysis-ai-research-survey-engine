"""Minimal, pluggable RAG retriever.

Loads every .txt/.md file under a corpus directory, chunks it, and retrieves
the top_k chunks most relevant to a query. Uses sentence-transformers cosine
similarity when available; falls back to a dependency-free TF-IDF retrieval
so the pipeline still runs without a local embedding model installed.
"""

from __future__ import annotations

import math
import re
from collections import Counter
from dataclasses import dataclass
from pathlib import Path
from typing import List

try:
    from sentence_transformers import SentenceTransformer
    import numpy as np
    EMBEDDINGS_AVAILABLE = True
except ImportError:  # pragma: no cover - import-time only
    EMBEDDINGS_AVAILABLE = False


@dataclass
class Chunk:
    source: str
    text: str


def _load_chunks(corpus_path: Path, chunk_size: int, chunk_overlap: int) -> List[Chunk]:
    chunks: List[Chunk] = []
    files = sorted(corpus_path.rglob("*.txt")) + sorted(corpus_path.rglob("*.md"))
    for f in files:
        text = f.read_text(encoding="utf-8", errors="ignore")
        step = max(chunk_size - chunk_overlap, 1)
        for start in range(0, len(text), step):
            piece = text[start:start + chunk_size].strip()
            if piece:
                chunks.append(Chunk(source=str(f.relative_to(corpus_path)), text=piece))
    return chunks


def _tokenize(text: str) -> List[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


class TfidfRetriever:
    """Dependency-free fallback: cosine similarity over TF-IDF vectors."""

    def __init__(self, chunks: List[Chunk]) -> None:
        self.chunks = chunks
        self.doc_tokens = [_tokenize(c.text) for c in chunks]
        df: Counter = Counter()
        for toks in self.doc_tokens:
            df.update(set(toks))
        n = max(len(chunks), 1)
        self.idf = {t: math.log((n + 1) / (freq + 1)) + 1 for t, freq in df.items()}

    def _vector(self, tokens: List[str]) -> Counter:
        tf = Counter(tokens)
        return Counter({t: c * self.idf.get(t, 0.0) for t, c in tf.items()})

    @staticmethod
    def _cosine(a: Counter, b: Counter) -> float:
        common = set(a) & set(b)
        num = sum(a[t] * b[t] for t in common)
        da = math.sqrt(sum(v * v for v in a.values())) or 1e-9
        db = math.sqrt(sum(v * v for v in b.values())) or 1e-9
        return num / (da * db)

    def top_k(self, query: str, k: int) -> List[Chunk]:
        qvec = self._vector(_tokenize(query))
        scored = [
            (self._cosine(qvec, self._vector(toks)), chunk)
            for toks, chunk in zip(self.doc_tokens, self.chunks)
        ]
        scored.sort(key=lambda pair: pair[0], reverse=True)
        return [chunk for _, chunk in scored[:k]]


class EmbeddingRetriever:
    """Preferred backend: sentence-transformers cosine similarity."""

    def __init__(self, chunks: List[Chunk], model_name: str) -> None:
        self.chunks = chunks
        self.model = SentenceTransformer(model_name)
        self.embeddings = self.model.encode([c.text for c in chunks], normalize_embeddings=True)

    def top_k(self, query: str, k: int) -> List[Chunk]:
        qvec = self.model.encode([query], normalize_embeddings=True)[0]
        scores = self.embeddings @ qvec
        order = np.argsort(-scores)[:k]
        return [self.chunks[i] for i in order]


def build_retriever(corpus_path: str, chunk_size: int, chunk_overlap: int, embedding_model: str | None):
    path = Path(corpus_path)
    if not path.exists():
        raise FileNotFoundError(f"RAG corpus_path does not exist: {corpus_path}")
    chunks = _load_chunks(path, chunk_size, chunk_overlap)
    if not chunks:
        raise ValueError(f"RAG corpus_path has no .txt/.md content: {corpus_path}")
    if EMBEDDINGS_AVAILABLE and embedding_model:
        return EmbeddingRetriever(chunks, embedding_model)
    return TfidfRetriever(chunks)
