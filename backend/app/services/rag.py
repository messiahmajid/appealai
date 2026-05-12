import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path

import numpy as np
import structlog

from app.services.llm import generate_embedding, generate_embeddings

logger = structlog.get_logger()

CACHE_DIR = Path(os.getcwd()) / ".cache"
EMBEDDINGS_CACHE = CACHE_DIR / "guideline-embeddings.json"


@dataclass
class EmbeddedChunk:
    id: str
    text: str
    guideline_id: str
    title: str
    source: str
    embedding: list[float]


@dataclass
class RAGResult:
    text: str
    guideline_id: str
    title: str
    source: str
    score: float


_embedded_chunks: list[EmbeddedChunk] | None = None


def cosine_similarity(a: list[float], b: list[float]) -> float:
    a_arr = np.array(a)
    b_arr = np.array(b)
    dot = np.dot(a_arr, b_arr)
    norm = np.linalg.norm(a_arr) * np.linalg.norm(b_arr)
    if norm == 0:
        return 0.0
    return float(dot / norm)


def _load_cached_embeddings() -> list[EmbeddedChunk] | None:
    try:
        if EMBEDDINGS_CACHE.exists():
            data = json.loads(EMBEDDINGS_CACHE.read_text())
            if isinstance(data, list) and len(data) > 0 and "embedding" in data[0]:
                return [
                    EmbeddedChunk(
                        id=d["id"],
                        text=d["text"],
                        guideline_id=d.get("guidelineId", d.get("guideline_id", "")),
                        title=d["title"],
                        source=d["source"],
                        embedding=d["embedding"],
                    )
                    for d in data
                ]
    except Exception:
        pass
    return None


def _save_cached_embeddings(chunks: list[EmbeddedChunk]) -> None:
    try:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        # Save with camelCase keys for compatibility with the TS cache
        data = [
            {
                "id": c.id,
                "text": c.text,
                "guidelineId": c.guideline_id,
                "title": c.title,
                "source": c.source,
                "embedding": c.embedding,
            }
            for c in chunks
        ]
        EMBEDDINGS_CACHE.write_text(json.dumps(data))
    except Exception as e:
        logger.error("failed_to_save_embeddings_cache", error=str(e))


async def initialize_rag() -> None:
    global _embedded_chunks

    if _embedded_chunks is not None:
        return

    cached = _load_cached_embeddings()
    if cached:
        _embedded_chunks = cached
        logger.info("loaded_cached_embeddings", count=len(cached))
        return

    logger.info("generating_guideline_embeddings")
    from app.services.guidelines import get_guideline_chunks

    chunks = get_guideline_chunks()
    texts = [c.text for c in chunks]

    all_embeddings: list[list[float]] = []
    for i in range(0, len(texts), 10):
        batch = texts[i : i + 10]
        batch_embeddings = await generate_embeddings(batch)
        all_embeddings.extend(batch_embeddings)

    _embedded_chunks = [
        EmbeddedChunk(
            id=chunk.id,
            text=chunk.text,
            guideline_id=chunk.guideline_id,
            title=chunk.title,
            source=chunk.source,
            embedding=all_embeddings[i],
        )
        for i, chunk in enumerate(chunks)
    ]

    _save_cached_embeddings(_embedded_chunks)
    logger.info("generated_and_cached_embeddings", count=len(_embedded_chunks))


async def search_rag(query: str, top_k: int = 5) -> list[RAGResult]:
    global _embedded_chunks

    if not _embedded_chunks:
        await initialize_rag()

    if not _embedded_chunks:
        raise RuntimeError("RAG pipeline not initialized — no guideline embeddings available")

    query_embedding = await generate_embedding(query)

    scored = [
        RAGResult(
            text=chunk.text,
            guideline_id=chunk.guideline_id,
            title=chunk.title,
            source=chunk.source,
            score=cosine_similarity(query_embedding, chunk.embedding),
        )
        for chunk in _embedded_chunks
    ]

    scored.sort(key=lambda r: r.score, reverse=True)

    seen: set[str] = set()
    deduped: list[RAGResult] = []
    for result in scored:
        if result.guideline_id not in seen:
            seen.add(result.guideline_id)
            deduped.append(result)
        if len(deduped) >= top_k:
            break

    return deduped


def search_rag_fallback(query: str, top_k: int = 5) -> list[RAGResult]:
    import re
    from app.services.guidelines import get_guideline_chunks

    chunks = get_guideline_chunks()
    terms = [t for t in query.lower().split() if len(t) > 2]

    scored: list[RAGResult] = []
    for chunk in chunks:
        text = chunk.text.lower()
        score = 0.0
        for term in terms:
            escaped = re.escape(term)
            matches = len(re.findall(escaped, text))
            score += matches
        score = score / max(len(terms), 1)
        scored.append(
            RAGResult(
                text=chunk.text,
                guideline_id=chunk.guideline_id,
                title=chunk.title,
                source=chunk.source,
                score=score,
            )
        )

    scored.sort(key=lambda r: r.score, reverse=True)

    seen: set[str] = set()
    deduped: list[RAGResult] = []
    for result in scored:
        if result.score > 0 and result.guideline_id not in seen:
            seen.add(result.guideline_id)
            deduped.append(result)
        if len(deduped) >= top_k:
            break

    return deduped
