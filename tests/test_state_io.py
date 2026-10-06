from pathlib import Path

from monakshi_os.db import rows
from monakshi_os.state_io import import_state, normalize_status


def test_status_normalization():
    assert normalize_status("Completed") == "done"
    assert normalize_status("Waiting on External") == "waiting"
    assert normalize_status("Needs Founder Action") == "founder_action"


def test_private_state_import_is_idempotent(tmp_path: Path):
    db = tmp_path / "monakshi.db"
    payload = {
        "schema_version": 3,
        "suppliers": [
            {
                "name": "Private Demo Supplier",
                "status": "sampling",
                "blind_shipping": True,
                "private_label": True,
                "mixed_designs": True,
                "low_moq": True,
                "no_inventory_model": True,
                "sample_available": True,
                "source_score": 94,
                "source_tier": "AAA",
            }
        ],
        "supplier_channels": [
            {
                "supplier_name": "Private Demo Supplier",
                "channel_type": "instagram",
                "handle": "@private_demo",
                "status": "active",
                "is_primary": True,
                "last_verified_at": "2026-10-06",
            }
        ],
        "supplier_aliases": [
            {
                "supplier_name": "Private Demo Supplier",
                "alias_type": "instagram",
                "alias": "@private_demo",
            }
        ],
        "products": [
            {
                "supplier_name": "Private Demo Supplier",
                "name": "Lotus Test",
                "category": "Urli",
                "launch_status": "candidate",
            }
        ],
        "launch_tasks": [
            {
                "source_id": "S01",
                "area": "Suppliers",
                "task": "Lock launch suppliers",
                "status": "Completed",
                "owner": "Founder",
            }
        ],
    }

    first = import_state(payload, db)
    second = import_state(payload, db)

    assert first == {"suppliers": 1, "products": 1, "launch_tasks": 1, "channels": 1, "aliases": 1, "evidence": 0}
    assert second == first
    assert len(rows("SELECT * FROM suppliers WHERE name=?", ("Private Demo Supplier",), db)) == 1
    assert len(rows("SELECT * FROM products WHERE name=?", ("Lotus Test",), db)) == 1
    task = rows("SELECT * FROM launch_tasks WHERE source_id=?", ("S01",), db)[0]
    assert task["status"] == "done"
