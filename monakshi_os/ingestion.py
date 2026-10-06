from __future__ import annotations

import hashlib
import json
import re
from typing import Any

from .db import connect, init_db
from .evidence import upsert_evidence
from .vault import ingest_text

EMAIL_RE = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.I)
URL_RE = re.compile(r"https?://\S+|www\.\S+", re.I)
PHONE_RE = re.compile(r"(?<!\w)(?:\+?\d[\d\s()\-]{7,}\d)(?!\w)")


def redact_text(value: str | None) -> str:
    text = (value or "").strip()
    text = EMAIL_RE.sub("[email]", text)
    text = URL_RE.sub("[url]", text)
    text = PHONE_RE.sub("[phone]", text)
    return text


def _hash_text(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8", errors="ignore")).hexdigest()


def _canonical_hash(record: dict[str, Any]) -> str:
    payload = {
        "entity_type": record.get("entity_type", "supplier"),
        "entity_name": record.get("entity_name", ""),
        "subject": record.get("subject", ""),
        "summary": record.get("summary", ""),
        "facts": record.get("facts", {}),
        "vault_text": record.get("vault_text", ""),
    }
    return _hash_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, default=str))


def _external_id(record: dict[str, Any]) -> str:
    source_system = (record.get("source_system") or record.get("source_type") or "manual").strip().lower()
    raw = str(record.get("external_id") or "").strip()
    if not raw:
        raise ValueError("external_id is required for connector ingestion")
    prefix = f"{source_system}:"
    return raw if raw.lower().startswith(prefix) else prefix + raw


def ingestion_log(db_path="data/monakshi.db") -> list[dict[str, Any]]:
    init_db(db_path)
    with connect(db_path) as con:
        return [
            dict(r)
            for r in con.execute(
                """SELECT * FROM ingestion_log
                   ORDER BY created_at DESC, id DESC"""
            ).fetchall()
        ]


def _is_duplicate(external_id: str, source_system: str, entity_name: str, content_hash: str, db_path: str) -> bool:
    with connect(db_path) as con:
        if con.execute("SELECT 1 FROM ingestion_log WHERE external_id=?", (external_id,)).fetchone():
            return True
        if con.execute(
            """SELECT 1 FROM ingestion_log
               WHERE source_system=? AND entity_name=? AND content_sha256=? AND status='imported'
               LIMIT 1""",
            (source_system, entity_name, content_hash),
        ).fetchone():
            return True
    return False


def _log_record(
    *,
    external_id: str,
    source_system: str,
    entity_name: str,
    artifact_type: str,
    content_hash: str,
    source_ref: str,
    redacted_label: str,
    occurred_at: str,
    status: str,
    notes: str,
    db_path: str,
) -> None:
    ref_hash = _hash_text(source_ref) if source_ref else ""
    with connect(db_path) as con:
        con.execute(
            """INSERT INTO ingestion_log(
                external_id, source_system, entity_name, artifact_type,
                content_sha256, source_ref_sha256, redacted_label,
                occurred_at, status, notes
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(external_id) DO UPDATE SET
                source_system=excluded.source_system,
                entity_name=excluded.entity_name,
                artifact_type=excluded.artifact_type,
                content_sha256=excluded.content_sha256,
                source_ref_sha256=excluded.source_ref_sha256,
                redacted_label=excluded.redacted_label,
                occurred_at=excluded.occurred_at,
                status=excluded.status,
                notes=excluded.notes""",
            (
                external_id,
                source_system,
                entity_name,
                artifact_type,
                content_hash,
                ref_hash,
                redacted_label,
                occurred_at,
                status,
                notes,
            ),
        )


def ingest_connector_records(records: list[dict[str, Any]], db_path="data/monakshi.db") -> dict[str, int]:
    init_db(db_path)
    result = {"selected": len(records), "imported": 0, "duplicates": 0, "vault_chunks": 0}

    for record in records:
        source_system = (record.get("source_system") or record.get("source_type") or "manual").strip().lower()
        entity_name = str(record.get("entity_name") or "").strip()
        summary = str(record.get("summary") or "").strip()
        if not entity_name:
            raise ValueError("entity_name is required")
        if not summary:
            raise ValueError("summary is required")

        external_id = _external_id(record)
        content_hash = _canonical_hash(record)
        artifact_type = str(record.get("artifact_type") or ("email" if source_system == "gmail" else "file")).strip().lower()
        source_ref = str(record.get("source_ref") or "").strip()
        occurred_at = str(record.get("occurred_at") or "").strip()
        label = redact_text(str(record.get("source_label") or record.get("subject") or artifact_type))
        notes = redact_text(str(record.get("log_notes") or ""))

        if _is_duplicate(external_id, source_system, entity_name, content_hash, db_path):
            result["duplicates"] += 1
            continue

        evidence_record = {
            "external_id": external_id,
            "entity_type": record.get("entity_type", "supplier"),
            "entity_name": entity_name,
            "source_type": source_system,
            "source_label": record.get("source_label", ""),
            "source_ref": source_ref,
            "occurred_at": occurred_at,
            "subject": record.get("subject", ""),
            "summary": summary,
            "facts": record.get("facts", {}),
            "decision_impact": record.get("decision_impact", ""),
            "confidence": record.get("confidence", "direct"),
        }
        upsert_evidence(evidence_record, db_path)

        vault_text = str(record.get("vault_text") or "").strip()
        if vault_text:
            source_name = str(record.get("vault_source_name") or f"{source_system}_{external_id.replace(':', '_')}.txt")
            result["vault_chunks"] += ingest_text(source_name, vault_text, db_path)

        _log_record(
            external_id=external_id,
            source_system=source_system,
            entity_name=entity_name,
            artifact_type=artifact_type,
            content_hash=content_hash,
            source_ref=source_ref,
            redacted_label=label,
            occurred_at=occurred_at,
            status="imported",
            notes=notes,
            db_path=db_path,
        )
        result["imported"] += 1

    return result


def import_ingestion_log(records: list[dict[str, Any]], db_path="data/monakshi.db") -> int:
    init_db(db_path)
    with connect(db_path) as con:
        for row in records:
            con.execute(
                """INSERT INTO ingestion_log(
                    external_id, source_system, entity_name, artifact_type,
                    content_sha256, source_ref_sha256, redacted_label,
                    occurred_at, status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(external_id) DO UPDATE SET
                    source_system=excluded.source_system,
                    entity_name=excluded.entity_name,
                    artifact_type=excluded.artifact_type,
                    content_sha256=excluded.content_sha256,
                    source_ref_sha256=excluded.source_ref_sha256,
                    redacted_label=excluded.redacted_label,
                    occurred_at=excluded.occurred_at,
                    status=excluded.status,
                    notes=excluded.notes""",
                (
                    row["external_id"],
                    row.get("source_system", "manual"),
                    row.get("entity_name", ""),
                    row.get("artifact_type", "record"),
                    row.get("content_sha256", ""),
                    row.get("source_ref_sha256", ""),
                    redact_text(row.get("redacted_label", "")),
                    row.get("occurred_at", ""),
                    row.get("status", "imported"),
                    redact_text(row.get("notes", "")),
                ),
            )
    return len(records)
