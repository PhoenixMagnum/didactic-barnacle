from __future__ import annotations

from collections import defaultdict
from datetime import datetime, timezone
from typing import Any

from .db import connect, init_db

VALID_DECISION_STATUS = {"locked", "working", "pending", "superseded"}
ACTIVE_DECISION_STATUS = {"locked", "working"}

SOURCE_AUTHORITY = {
    1: "Founder locks / newest explicit founder decisions",
    2: "Current controlling Launch Command Centre",
    3: "Approved current operating / brand documents",
    4: "Written supplier, customer, payment or store evidence",
    5: "Live connected-system state",
    6: "Current research / working notes",
    7: "Historical / superseded material",
    8: "Memory",
}


def _parse_when(value: str | None) -> datetime | None:
    if not value:
        return None
    raw = str(value).strip()
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    except ValueError:
        try:
            dt = datetime.strptime(raw[:10], "%Y-%m-%d")
        except ValueError:
            return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def source_is_stale(source: dict[str, Any], now: datetime | None = None) -> bool:
    if source.get("status") == "superseded":
        return False
    when = _parse_when(source.get("last_verified_at"))
    if not when:
        return True
    freshness_days = int(source.get("freshness_days") or 30)
    now = now or datetime.now(timezone.utc)
    if now.tzinfo is None:
        now = now.replace(tzinfo=timezone.utc)
    return (now.astimezone(timezone.utc) - when).days > freshness_days


def upsert_source(record: dict[str, Any], db_path="data/monakshi.db") -> None:
    init_db(db_path)
    source_id = record["source_id"].strip()
    authority_rank = int(record.get("authority_rank") or 8)
    if authority_rank not in SOURCE_AUTHORITY:
        raise ValueError("authority_rank must be between 1 and 8")
    with connect(db_path) as con:
        con.execute(
            """INSERT INTO source_registry(
                source_id, name, source_type, authority_rank, version, location,
                is_controlling, last_verified_at, freshness_days, status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(source_id) DO UPDATE SET
                name=excluded.name,
                source_type=excluded.source_type,
                authority_rank=excluded.authority_rank,
                version=excluded.version,
                location=excluded.location,
                is_controlling=excluded.is_controlling,
                last_verified_at=excluded.last_verified_at,
                freshness_days=excluded.freshness_days,
                status=excluded.status,
                notes=excluded.notes,
                updated_at=CURRENT_TIMESTAMP""",
            (
                source_id,
                record.get("name", source_id),
                record.get("source_type", "other"),
                authority_rank,
                record.get("version", ""),
                record.get("location", ""),
                int(bool(record.get("is_controlling"))),
                record.get("last_verified_at", ""),
                int(record.get("freshness_days") or 30),
                record.get("status", "active"),
                record.get("notes", ""),
            ),
        )


def source_registry(db_path="data/monakshi.db") -> list[dict[str, Any]]:
    init_db(db_path)
    with connect(db_path) as con:
        return [
            dict(r)
            for r in con.execute(
                """SELECT * FROM source_registry
                   ORDER BY authority_rank, is_controlling DESC, updated_at DESC, name"""
            ).fetchall()
        ]


def upsert_decision(
    record: dict[str, Any],
    db_path="data/monakshi.db",
    supersede_prior: bool = False,
) -> None:
    init_db(db_path)
    status = record.get("status", "working")
    if status not in VALID_DECISION_STATUS:
        status = "pending"
    decision_id = record["decision_id"].strip()
    decision_key = record["decision_key"].strip()

    with connect(db_path) as con:
        if supersede_prior and status in ACTIVE_DECISION_STATUS:
            con.execute(
                """UPDATE decision_canon
                   SET status='superseded', updated_at=CURRENT_TIMESTAMP
                   WHERE decision_key=? AND decision_id<>? AND status IN ('locked','working')""",
                (decision_key, decision_id),
            )
        con.execute(
            """INSERT INTO decision_canon(
                decision_id, domain, decision_key, decision_value, status,
                source_id, effective_date, rationale, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(decision_id) DO UPDATE SET
                domain=excluded.domain,
                decision_key=excluded.decision_key,
                decision_value=excluded.decision_value,
                status=excluded.status,
                source_id=excluded.source_id,
                effective_date=excluded.effective_date,
                rationale=excluded.rationale,
                notes=excluded.notes,
                updated_at=CURRENT_TIMESTAMP""",
            (
                decision_id,
                record.get("domain", "general"),
                decision_key,
                str(record.get("decision_value", "")),
                status,
                record.get("source_id"),
                record.get("effective_date", ""),
                record.get("rationale", ""),
                record.get("notes", ""),
            ),
        )


def decision_canon(db_path="data/monakshi.db") -> list[dict[str, Any]]:
    init_db(db_path)
    with connect(db_path) as con:
        return [
            dict(r)
            for r in con.execute(
                """SELECT d.*, s.name source_name, s.authority_rank, s.status source_status
                   FROM decision_canon d
                   LEFT JOIN source_registry s ON s.source_id=d.source_id
                   ORDER BY
                     CASE d.status WHEN 'locked' THEN 0 WHEN 'working' THEN 1 WHEN 'pending' THEN 2 ELSE 3 END,
                     COALESCE(s.authority_rank, 99),
                     d.effective_date DESC,
                     d.updated_at DESC"""
            ).fetchall()
        ]


def resolve_current_decision(decision_key: str, db_path="data/monakshi.db") -> dict | None:
    init_db(db_path)
    with connect(db_path) as con:
        row = con.execute(
            """SELECT d.*, s.name source_name, s.authority_rank
               FROM decision_canon d
               LEFT JOIN source_registry s ON s.source_id=d.source_id
               WHERE d.decision_key=? AND d.status IN ('locked','working')
               ORDER BY
                 COALESCE(s.authority_rank, 99) ASC,
                 CASE d.status WHEN 'locked' THEN 0 ELSE 1 END ASC,
                 d.effective_date DESC,
                 d.updated_at DESC
               LIMIT 1""",
            (decision_key,),
        ).fetchone()
    return dict(row) if row else None


def decision_conflicts(db_path="data/monakshi.db") -> list[dict[str, Any]]:
    active = [d for d in decision_canon(db_path) if d["status"] in ACTIVE_DECISION_STATUS]
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    for row in active:
        grouped[row["decision_key"]].append(row)

    conflicts = []
    for key, items in grouped.items():
        values = {str(x.get("decision_value", "")).strip() for x in items}
        if len(values) <= 1:
            continue
        winner = resolve_current_decision(key, db_path)
        conflicts.append(
            {
                "decision_key": key,
                "values": sorted(values),
                "records": items,
                "current": winner,
            }
        )
    return conflicts


def import_canon_state(
    sources: list[dict[str, Any]],
    decisions: list[dict[str, Any]],
    db_path="data/monakshi.db",
) -> dict[str, int]:
    for source in sources:
        upsert_source(source, db_path)
    for decision in decisions:
        upsert_decision(decision, db_path)
    return {"sources": len(sources), "decisions": len(decisions)}
