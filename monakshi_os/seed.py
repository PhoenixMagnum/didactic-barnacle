from __future__ import annotations

from .db import connect, init_db

DEMO_SUPPLIERS = [
    {
        "name": "Demo Atelier A",
        "contact_channel": "Instagram",
        "status": "sampling",
        "blind_shipping": 1,
        "private_label": 1,
        "mixed_designs": 1,
        "low_moq": 1,
        "no_inventory_model": 1,
        "sample_available": 1,
        "quality_score": 8,
        "aesthetic_score": 9,
        "commercial_score": 8,
        "reliability_score": 8,
        "notes": "Safe demo record. Replace locally with real supplier data.",
    },
    {
        "name": "Demo Atelier B",
        "contact_channel": "Email",
        "status": "discovered",
        "blind_shipping": 0,
        "private_label": 1,
        "mixed_designs": 1,
        "low_moq": 0,
        "no_inventory_model": 0,
        "sample_available": 1,
        "quality_score": 7,
        "aesthetic_score": 8,
        "commercial_score": 6,
        "reliability_score": 6,
        "notes": "Safe demo record.",
    },
]

def seed_demo(db_path="data/monakshi.db"):
    init_db(db_path)
    with connect(db_path) as con:
        for s in DEMO_SUPPLIERS:
            cols = ", ".join(s.keys())
            marks = ", ".join("?" for _ in s)
            con.execute(
                f"INSERT OR IGNORE INTO suppliers({cols}) VALUES ({marks})",
                tuple(s.values()),
            )
        supplier = con.execute(
            "SELECT id FROM suppliers WHERE name='Demo Atelier A'"
        ).fetchone()
        if supplier:
            con.execute(
                """INSERT OR IGNORE INTO products(
                    supplier_id, name, category, supplier_price, target_retail,
                    shipping_cost, packaging_cost, payment_fee_pct, sample_status,
                    burn_test_pass, packaging_test_pass, photo_approved, specs_verified, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    supplier["id"], "Demo Lotus Urli", "Urli", 180, 499,
                    60, 20, 2.0, "approved", 1, 1, 1, 1,
                    "Illustrative economics only. Do not publish."
                ),
            )
