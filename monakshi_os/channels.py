from __future__ import annotations

from datetime import datetime, timezone
import re
from typing import Any

from .db import connect, init_db


def normalize_alias(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "", (value or "").strip().lower())


def add_channel(
    supplier_id: int,
    channel_type: str,
    handle: str = "",
    profile_url: str = "",
    status: str = "active",
    is_primary: bool = False,
    last_verified_at: str = "",
    notes: str = "",
    db_path="data/monakshi.db",
) -> None:
    init_db(db_path)
    channel_type = channel_type.strip().lower()
    handle = handle.strip()
    with connect(db_path) as con:
        if is_primary:
            con.execute("UPDATE supplier_channels SET is_primary=0 WHERE supplier_id=?", (supplier_id,))
        con.execute(
            """INSERT INTO supplier_channels(
                supplier_id, channel_type, handle, profile_url, status,
                is_primary, last_verified_at, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(supplier_id, channel_type, handle) DO UPDATE SET
                profile_url=excluded.profile_url,
                status=excluded.status,
                is_primary=excluded.is_primary,
                last_verified_at=excluded.last_verified_at,
                notes=excluded.notes,
                updated_at=CURRENT_TIMESTAMP""",
            (
                supplier_id, channel_type, handle, profile_url.strip(), status.strip(),
                int(bool(is_primary)), last_verified_at.strip(), notes.strip(),
            ),
        )


def add_alias(
    supplier_id: int,
    alias: str,
    alias_type: str = "name",
    db_path="data/monakshi.db",
) -> None:
    init_db(db_path)
    alias = alias.strip()
    normalized = normalize_alias(alias)
    if not normalized:
        return
    with connect(db_path) as con:
        con.execute(
            """INSERT INTO supplier_aliases(supplier_id, alias, alias_type, normalized_alias)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(alias_type, normalized_alias) DO UPDATE SET
                   supplier_id=excluded.supplier_id,
                   alias=excluded.alias""",
            (supplier_id, alias, alias_type.strip().lower(), normalized),
        )


def supplier_channels(db_path="data/monakshi.db") -> list[dict[str, Any]]:
    init_db(db_path)
    with connect(db_path) as con:
        return [
            dict(r)
            for r in con.execute(
                """SELECT c.*, s.name supplier_name
                   FROM supplier_channels c
                   JOIN suppliers s ON s.id=c.supplier_id
                   ORDER BY s.name, c.is_primary DESC, c.channel_type, c.handle"""
            ).fetchall()
        ]


def supplier_aliases(db_path="data/monakshi.db") -> list[dict[str, Any]]:
    init_db(db_path)
    with connect(db_path) as con:
        return [
            dict(r)
            for r in con.execute(
                """SELECT a.*, s.name supplier_name
                   FROM supplier_aliases a
                   JOIN suppliers s ON s.id=a.supplier_id
                   ORDER BY s.name, a.alias_type, a.alias"""
            ).fetchall()
        ]


def resolve_supplier(alias: str, alias_type: str | None = None, db_path="data/monakshi.db") -> dict | None:
    init_db(db_path)
    normalized = normalize_alias(alias)
    if not normalized:
        return None
    with connect(db_path) as con:
        if alias_type:
            row = con.execute(
                """SELECT s.* FROM supplier_aliases a
                   JOIN suppliers s ON s.id=a.supplier_id
                   WHERE a.alias_type=? AND a.normalized_alias=?""",
                (alias_type.strip().lower(), normalized),
            ).fetchone()
        else:
            row = con.execute(
                """SELECT s.* FROM supplier_aliases a
                   JOIN suppliers s ON s.id=a.supplier_id
                   WHERE a.normalized_alias=?
                   ORDER BY CASE a.alias_type
                       WHEN 'instagram' THEN 1
                       WHEN 'whatsapp' THEN 2
                       WHEN 'email' THEN 3
                       ELSE 4 END
                   LIMIT 1""",
                (normalized,),
            ).fetchone()
    return dict(row) if row else None


def channel_is_stale(last_verified_at: str | None, days: int = 60) -> bool:
    if not last_verified_at:
        return True
    raw = last_verified_at.strip()
    try:
        when = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        try:
            when = datetime.strptime(raw[:10], "%Y-%m-%d").replace(tzinfo=timezone.utc)
        except ValueError:
            return True
    if when.tzinfo is None:
        when = when.replace(tzinfo=timezone.utc)
    age = datetime.now(timezone.utc) - when.astimezone(timezone.utc)
    return age.days > days


def import_channel_state(
    channels: list[dict[str, Any]],
    aliases: list[dict[str, Any]],
    db_path="data/monakshi.db",
) -> dict[str, int]:
    init_db(db_path)
    with connect(db_path) as con:
        ids = {r["name"]: r["id"] for r in con.execute("SELECT id, name FROM suppliers").fetchall()}
    channel_count = 0
    alias_count = 0
    for row in channels:
        supplier_id = ids.get(row.get("supplier_name", ""))
        if not supplier_id:
            continue
        add_channel(
            supplier_id=supplier_id,
            channel_type=row.get("channel_type", "other"),
            handle=row.get("handle", ""),
            profile_url=row.get("profile_url", ""),
            status=row.get("status", "active"),
            is_primary=bool(row.get("is_primary")),
            last_verified_at=row.get("last_verified_at", ""),
            notes=row.get("notes", ""),
            db_path=db_path,
        )
        channel_count += 1
    for row in aliases:
        supplier_id = ids.get(row.get("supplier_name", ""))
        if not supplier_id:
            continue
        add_alias(
            supplier_id=supplier_id,
            alias=row.get("alias", ""),
            alias_type=row.get("alias_type", "name"),
            db_path=db_path,
        )
        alias_count += 1
    return {"channels": channel_count, "aliases": alias_count}
