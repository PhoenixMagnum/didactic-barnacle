from __future__ import annotations

import hashlib
import re
from datetime import datetime, timezone

import requests
from bs4 import BeautifulSoup

from .db import connect

UA = "HouseOfMonakshiScout/1.0 (+founder-operated research)"

def fetch_page(url: str, timeout: int = 20) -> dict:
    r = requests.get(url, timeout=timeout, headers={"User-Agent": UA})
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    title = (soup.title.string or "").strip() if soup.title else url
    text = re.sub(r"\s+", " ", soup.get_text(" ", strip=True))
    excerpt = text[:1400]
    digest = hashlib.sha256(text.encode("utf-8", errors="ignore")).hexdigest()
    return {"title": title[:300], "text": text, "excerpt": excerpt, "hash": digest}

def add_watch(label: str, url: str, db_path="data/monakshi.db") -> None:
    with connect(db_path) as con:
        con.execute(
            "INSERT OR IGNORE INTO watches(label, url) VALUES (?, ?)",
            (label.strip(), url.strip()),
        )

def check_watch(watch_id: int, db_path="data/monakshi.db") -> dict:
    with connect(db_path) as con:
        row = con.execute("SELECT * FROM watches WHERE id=?", (watch_id,)).fetchone()
        if not row:
            raise ValueError("Watch not found")
        watch = dict(row)
        current = fetch_page(watch["url"])
        now = datetime.now(timezone.utc).isoformat()
        changed = bool(watch["last_hash"] and watch["last_hash"] != current["hash"])
        if changed:
            con.execute(
                "INSERT INTO watch_events(watch_id, change_type, old_value, new_value) VALUES (?, ?, ?, ?)",
                (watch_id, "page_changed", watch["last_excerpt"] or "", current["excerpt"]),
            )
        con.execute(
            """UPDATE watches
               SET last_hash=?, last_title=?, last_excerpt=?, last_checked_at=?
               WHERE id=?""",
            (current["hash"], current["title"], current["excerpt"], now, watch_id),
        )
    return {"changed": changed, **current}
