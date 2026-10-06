from __future__ import annotations

import re
from pathlib import Path

from pypdf import PdfReader

from .db import connect

def _read(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        reader = PdfReader(str(path))
        return "\n\n".join((p.extract_text() or "") for p in reader.pages)
    if suffix in {".txt", ".md", ".csv"}:
        return path.read_text(encoding="utf-8", errors="ignore")
    raise ValueError("Supported vault formats: PDF, TXT, MD, CSV")

def chunk_text(text: str, size: int = 1100, overlap: int = 180) -> list[str]:
    text = re.sub(r"\s+", " ", text).strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = min(start + size, len(text))
        chunks.append(text[start:end])
        if end == len(text):
            break
        start = max(start + 1, end - overlap)
    return chunks

def ingest_text(source_name: str, text: str, db_path="data/monakshi.db") -> int:
    chunks = chunk_text(text)
    with connect(db_path) as con:
        con.execute("DELETE FROM documents WHERE source_name = ?", (source_name,))
        con.executemany(
            "INSERT INTO documents(source_name, chunk_index, content) VALUES (?, ?, ?)",
            [(source_name, i + 1, c) for i, c in enumerate(chunks)],
        )
    return len(chunks)

def ingest(path: Path, db_path="data/monakshi.db") -> int:
    return ingest_text(path.name, _read(path), db_path)

def search(query: str, limit: int = 8, db_path="data/monakshi.db") -> list[dict]:
    terms = [t.lower() for t in re.findall(r"[A-Za-z0-9₹%.-]+", query) if len(t) > 1]
    if not terms:
        return []
    with connect(db_path) as con:
        docs = [dict(r) for r in con.execute("SELECT * FROM documents").fetchall()]
    scored = []
    for d in docs:
        hay = d["content"].lower()
        score = sum(hay.count(t) for t in terms)
        if score:
            d["score"] = score
            d["citation"] = f'{d["source_name"]} · chunk {d["chunk_index"]}'
            scored.append(d)
    return sorted(scored, key=lambda x: x["score"], reverse=True)[:limit]
