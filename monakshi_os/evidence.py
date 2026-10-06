from __future__ import annotations

import json
from typing import Any

from .db import connect, init_db

VALID_CONFIDENCE = {"direct", "derived", "unverified"}

def upsert_evidence(record: dict[str, Any], db_path="data/monakshi.db") -> None:
    init_db(db_path)
    external_id = record.get("external_id")
    params = (
        external_id,
        record.get("entity_type", "supplier"),
        record["entity_name"],
        record.get("source_type", "manual"),
        record.get("source_label", ""),
        record.get("source_ref", ""),
        record.get("occurred_at", ""),
        record.get("subject", ""),
        record["summary"],
        json.dumps(record.get("facts", {}), ensure_ascii=False, sort_keys=True),
        record.get("decision_impact", ""),
        record.get("confidence", "direct") if record.get("confidence", "direct") in VALID_CONFIDENCE else "unverified",
    )
    with connect(db_path) as con:
        if external_id:
            existing = con.execute(
                "SELECT id FROM evidence_records WHERE external_id=?",
                (external_id,),
            ).fetchone()
            if existing:
                con.execute(
                    """UPDATE evidence_records SET
                        entity_type=?, entity_name=?, source_type=?, source_label=?,
                        source_ref=?, occurred_at=?, subject=?, summary=?, facts_json=?,
                        decision_impact=?, confidence=?
                       WHERE external_id=?""",
                    (
                        params[1], params[2], params[3], params[4], params[5], params[6],
                        params[7], params[8], params[9], params[10], params[11], external_id,
                    ),
                )
                return
        con.execute(
            """INSERT INTO evidence_records(
                external_id, entity_type, entity_name, source_type, source_label,
                source_ref, occurred_at, subject, summary, facts_json,
                decision_impact, confidence
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            params,
        )

def import_evidence(records: list[dict[str, Any]], db_path="data/monakshi.db") -> int:
    for record in records:
        upsert_evidence(record, db_path)
    return len(records)

def search_evidence(query: str = "", entity_name: str = "", db_path="data/monakshi.db") -> list[dict]:
    init_db(db_path)
    where = []
    params: list[Any] = []
    if entity_name:
        where.append("entity_name = ?")
        params.append(entity_name)
    if query.strip():
        q = f"%{query.strip()}%"
        where.append(
            "(entity_name LIKE ? OR subject LIKE ? OR summary LIKE ? OR facts_json LIKE ? OR decision_impact LIKE ?)"
        )
        params.extend([q, q, q, q, q])
    sql = "SELECT * FROM evidence_records"
    if where:
        sql += " WHERE " + " AND ".join(where)
    sql += " ORDER BY occurred_at DESC, id DESC"
    with connect(db_path) as con:
        result = [dict(r) for r in con.execute(sql, tuple(params)).fetchall()]
    for row in result:
        try:
            row["facts"] = json.loads(row.pop("facts_json") or "{}")
        except json.JSONDecodeError:
            row["facts"] = {}
    return result

def entity_facts(entity_name: str, db_path="data/monakshi.db") -> dict[str, list[Any]]:
    merged: dict[str, list[Any]] = {}
    for row in reversed(search_evidence(entity_name=entity_name, db_path=db_path)):
        for key, value in row.get("facts", {}).items():
            if value is None or value == "":
                continue
            merged.setdefault(key, [])
            if value not in merged[key]:
                merged[key].append(value)
    return merged
