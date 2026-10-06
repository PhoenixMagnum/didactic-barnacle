from pathlib import Path

from monakshi_os.evidence import entity_facts, import_evidence, search_evidence


def test_evidence_import_is_idempotent(tmp_path: Path):
    db = tmp_path / "monakshi.db"
    records = [
        {
            "external_id": "gmail:test-1",
            "entity_type": "supplier",
            "entity_name": "Test Supplier",
            "source_type": "gmail",
            "source_label": "Supplier reply",
            "occurred_at": "2026-10-06T03:52:52+05:30",
            "subject": "Re: wholesale enquiry",
            "summary": "Supplier confirmed MOQ 10 per design and unbranded supply.",
            "facts": {"moq_per_design": 10, "unbranded_supply": True},
            "decision_impact": "Not suitable for mixed-SKU zero-inventory launch.",
            "confidence": "direct",
        }
    ]
    assert import_evidence(records, db) == 1
    assert import_evidence(records, db) == 1

    found = search_evidence(entity_name="Test Supplier", db_path=db)
    assert len(found) == 1
    assert found[0]["facts"]["moq_per_design"] == 10

    facts = entity_facts("Test Supplier", db)
    assert facts["unbranded_supply"] == [True]
