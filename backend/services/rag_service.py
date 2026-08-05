"""Local Markdown-to-FAISS retrieval for scam detection explanations."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import faiss
import numpy as np
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sentence_transformers import SentenceTransformer

BASE_DIR = Path(__file__).resolve().parents[1]
KNOWLEDGE_PATH = BASE_DIR / "knowledge_base"
VECTORSTORE_PATH = BASE_DIR / "vectorstore" / "faiss_index"
INDEX_PATH = VECTORSTORE_PATH / "index.faiss"
METADATA_PATH = VECTORSTORE_PATH / "chunks.json"
MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"

_embedding_model: SentenceTransformer | None = None
_index: faiss.Index | None = None
_chunks: list[dict[str, str]] | None = None


def load_documents() -> list[dict[str, str]]:
    """Recursively load non-empty Markdown documents with stable relative paths."""
    documents = []
    for file_path in KNOWLEDGE_PATH.rglob("*.md"):
        content = file_path.read_text(encoding="utf-8").strip()
        if content:
            documents.append({
                "source": file_path.relative_to(BASE_DIR).as_posix(),
                "content": content,
            })
    return documents


def split_documents(documents: list[dict[str, str]]) -> list[dict[str, str]]:
    splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=100)
    chunks = []
    for document in documents:
        for chunk_number, content in enumerate(splitter.split_text(document["content"])):
            chunks.append({
                "source": document["source"],
                "content": content,
                "chunk_number": str(chunk_number),
            })
    return chunks


def get_embedding_model() -> SentenceTransformer:
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(MODEL_NAME)
    return _embedding_model


def create_vector_database() -> dict[str, Any]:
    """Build and persist a normalized inner-product FAISS index locally."""
    global _index, _chunks
    documents = load_documents()
    chunks = split_documents(documents)
    if not chunks:
        raise RuntimeError(f"No non-empty Markdown documents found in {KNOWLEDGE_PATH}")

    embeddings = get_embedding_model().encode(
        [chunk["content"] for chunk in chunks],
        convert_to_numpy=True,
        normalize_embeddings=True,
        show_progress_bar=True,
    ).astype("float32")

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)
    VECTORSTORE_PATH.mkdir(parents=True, exist_ok=True)
    faiss.write_index(index, str(INDEX_PATH))
    METADATA_PATH.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")

    _index, _chunks = index, chunks
    return {"documents": len(documents), "chunks": len(chunks), "index_path": str(INDEX_PATH)}


def load_vector_database() -> tuple[faiss.Index, list[dict[str, str]]]:
    """Load the persisted FAISS index and matching chunk metadata."""
    global _index, _chunks
    if _index is not None and _chunks is not None:
        return _index, _chunks
    if not INDEX_PATH.exists() or not METADATA_PATH.exists():
        raise FileNotFoundError("FAISS index not found. Run: python create_vector_db.py")
    _index = faiss.read_index(str(INDEX_PATH))
    _chunks = json.loads(METADATA_PATH.read_text(encoding="utf-8"))
    return _index, _chunks


def retrieve_context(query: str, k: int = 3) -> list[dict[str, Any]]:
    """Return the top relevant knowledge chunks and their cosine-similarity score."""
    index, chunks = load_vector_database()
    if not query.strip():
        return []
    k = min(max(1, k), len(chunks))
    query_embedding = get_embedding_model().encode(
        [query], convert_to_numpy=True, normalize_embeddings=True
    ).astype("float32")
    scores, positions = index.search(query_embedding, k)
    return [
        {**chunks[position], "score": round(float(score), 4)}
        for score, position in zip(scores[0], positions[0])
        if position >= 0
    ]
