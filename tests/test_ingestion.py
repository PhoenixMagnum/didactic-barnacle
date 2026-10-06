from pathlib import Path

from monakshi_os.db import rows
from monakshi_os.ingestion import ingest_connector_records, ingestion_log, redact_text


def test_redaction():
    value = "Email vendor@example.com phone +91 99999 11111 see https://example.com/x"
    redacted = redact_text(value)
    assert "vendor@example.com" not in redacted
    assert "99999" not in redacted
    assert "https://" not in redacted


def test_connector_ingestion_is_deduplicated_and_searchable(tmp_path: Path):
    db = tmp_path / "monakshi.db"
    record = {
        "source_system": "gmail",
        "external_id": "msg-1",
        "entity_type": "supplier",
        "entity_name": "Example Supplier",
        "artifact_type": "email",
        "occurred_at": "2026-10-06",
        "subject": "Re: MOQ",
        "source_label": "MOQ confirmation from vendor@example.com",
        "source_ref": "private:gmail:msg-1",
        "summary": "Supplier confirmed MOQ 10 per design.",
        "facts": {"moq_per_design": 10},
        "decision_impact": "Not suitable for mixed 10-piece total trial.",
        "confidence": "direct",
        "vault_text": "Supplier confirmed MOQ 10 per design and unbranded supply.",
    }

    first = ingest_connector_records([record], str(db))
    second = ingest_connector_records([record], str(db))

    assert first["imported"] == 1
    assert first["vault_chunks"] >= 1
    assert second["duplicates"] == 1
    assert len(rows("SELECT * FROM evidence_records", path=db)) == 1
    logs = ingestion_log(str(db))
    assert len(logs) == 1
    assert "vendor@example.com" not in logs[0]["redacted_label"]
    assert logs[0]["external_id"] == "gmail:msg-1"
