from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .channels import import_channel_state, supplier_aliases, supplier_channels
from .db import connect, init_db
from .evidence import import_evidence, search_evidence
from .ingestion import import_ingestion_log, ingestion_log
from .source_canon import decision_canon, import_canon_state, source_registry

STATUS_MAP = {
    "not started": "todo",
    "in progress": "in_progress",
    "waiting on external": "waiting",
    "waiting on quotes": "waiting",
    "needs founder action": "founder_action",
    "completed": "done",
    "blocked": "blocked",
    "ready": "todo",
    "planned": "todo",
}

def normalize_status(value: str | None) -> str:
    if not value:
        return "todo"
    key = value.strip().lower()
    return STATUS_MAP.get(key, key.replace(" ", "_"))

def load_payload(path: str | Path) -> dict[str, Any]:
    return json.loads(Path(path).read_text(encoding="utf-8"))

def import_state(payload: dict[str, Any], db_path="data/monakshi.db") -> dict[str, int]:
    init_db(db_path)
    counts = {"sources": 0, "decisions": 0, "suppliers": 0, "products": 0, "launch_tasks": 0, "channels": 0, "aliases": 0, "evidence": 0, "ingestions": 0}

    canon_counts = import_canon_state(
        payload.get("sources", []),
        payload.get("decisions", []),
        db_path,
    )
    counts.update(canon_counts)

    with connect(db_path) as con:
        for s in payload.get("suppliers", []):
            con.execute(
                """INSERT INTO suppliers(
                    name, contact_channel, status, blind_shipping, private_label, mixed_designs,
                    low_moq, no_inventory_model, sample_available, quality_score, aesthetic_score,
                    commercial_score, reliability_score, source_score, source_tier, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(name) DO UPDATE SET
                    contact_channel=excluded.contact_channel,
                    status=excluded.status,
                    blind_shipping=excluded.blind_shipping,
                    private_label=excluded.private_label,
                    mixed_designs=excluded.mixed_designs,
                    low_moq=excluded.low_moq,
                    no_inventory_model=excluded.no_inventory_model,
                    sample_available=excluded.sample_available,
                    quality_score=excluded.quality_score,
                    aesthetic_score=excluded.aesthetic_score,
                    commercial_score=excluded.commercial_score,
                    reliability_score=excluded.reliability_score,
                    source_score=excluded.source_score,
                    source_tier=excluded.source_tier,
                    notes=excluded.notes,
                    updated_at=CURRENT_TIMESTAMP""",
                (
                    s["name"],
                    s.get("contact_channel", ""),
                    s.get("status", "discovered"),
                    int(bool(s.get("blind_shipping"))),
                    int(bool(s.get("private_label"))),
                    int(bool(s.get("mixed_designs"))),
                    int(bool(s.get("low_moq"))),
                    int(bool(s.get("no_inventory_model"))),
                    int(bool(s.get("sample_available", True))),
                    float(s.get("quality_score", 0) or 0),
                    float(s.get("aesthetic_score", 0) or 0),
                    float(s.get("commercial_score", 0) or 0),
                    float(s.get("reliability_score", 0) or 0),
                    s.get("source_score"),
                    s.get("source_tier", ""),
                    s.get("notes", ""),
                ),
            )
            counts["suppliers"] += 1

        supplier_ids = {
            row["name"]: row["id"]
            for row in con.execute("SELECT id, name FROM suppliers").fetchall()
        }

        for p in payload.get("products", []):
            supplier_id = supplier_ids.get(p.get("supplier_name", ""))
            con.execute(
                """INSERT INTO products(
                    supplier_id, name, category, supplier_price, target_retail,
                    shipping_cost, packaging_cost, payment_fee_pct, sample_status,
                    burn_test_pass, packaging_test_pass, photo_approved, specs_verified,
                    launch_status, notes
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(supplier_id, name) DO UPDATE SET
                    category=excluded.category,
                    supplier_price=COALESCE(excluded.supplier_price, products.supplier_price),
                    target_retail=COALESCE(excluded.target_retail, products.target_retail),
                    shipping_cost=excluded.shipping_cost,
                    packaging_cost=excluded.packaging_cost,
                    payment_fee_pct=excluded.payment_fee_pct,
                    sample_status=excluded.sample_status,
                    launch_status=excluded.launch_status,
                    notes=excluded.notes""",
                (
                    supplier_id,
                    p["name"],
                    p.get("category", ""),
                    p.get("supplier_price"),
                    p.get("target_retail"),
                    float(p.get("shipping_cost", 0) or 0),
                    float(p.get("packaging_cost", 0) or 0),
                    float(p.get("payment_fee_pct", 2.0) or 0),
                    p.get("sample_status", "not_requested"),
                    int(bool(p.get("burn_test_pass"))),
                    int(bool(p.get("packaging_test_pass"))),
                    int(bool(p.get("photo_approved"))),
                    int(bool(p.get("specs_verified"))),
                    p.get("launch_status", "candidate"),
                    p.get("notes", ""),
                ),
            )
            counts["products"] += 1

        for t in payload.get("launch_tasks", []):
            source_id = t.get("source_id")
            status = normalize_status(t.get("status"))
            blocker = t.get("blocker", "")
            params = (
                source_id,
                t.get("area", "General"),
                t["task"],
                status,
                blocker,
                t.get("owner", "Founder"),
                t.get("priority", ""),
                t.get("due_gate", ""),
                t.get("dependency", ""),
                t.get("next_action", ""),
                t.get("evidence", ""),
                t.get("notes", ""),
            )
            if source_id:
                existing = con.execute(
                    "SELECT id FROM launch_tasks WHERE source_id=?",
                    (source_id,),
                ).fetchone()
                if existing:
                    con.execute(
                        """UPDATE launch_tasks SET
                            area=?, task=?, status=?, blocker=?, owner=?, priority=?,
                            due_gate=?, dependency=?, next_action=?, evidence=?, notes=?
                           WHERE source_id=?""",
                        (
                            t.get("area", "General"),
                            t["task"],
                            status,
                            blocker,
                            t.get("owner", "Founder"),
                            t.get("priority", ""),
                            t.get("due_gate", ""),
                            t.get("dependency", ""),
                            t.get("next_action", ""),
                            t.get("evidence", ""),
                            t.get("notes", ""),
                            source_id,
                        ),
                    )
                else:
                    con.execute(
                        """INSERT INTO launch_tasks(
                            source_id, area, task, status, blocker, owner, priority, due_gate,
                            dependency, next_action, evidence, notes
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                        params,
                    )
            else:
                con.execute(
                    """INSERT INTO launch_tasks(
                        source_id, area, task, status, blocker, owner, priority, due_gate,
                        dependency, next_action, evidence, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(area, task) DO UPDATE SET
                        status=excluded.status,
                        blocker=excluded.blocker,
                        owner=excluded.owner,
                        priority=excluded.priority,
                        due_gate=excluded.due_gate,
                        dependency=excluded.dependency,
                        next_action=excluded.next_action,
                        evidence=excluded.evidence,
                        notes=excluded.notes""",
                    params,
                )
            counts["launch_tasks"] += 1

    channel_counts = import_channel_state(
        payload.get("supplier_channels", []),
        payload.get("supplier_aliases", []),
        db_path,
    )
    counts.update(channel_counts)
    counts["evidence"] = import_evidence(payload.get("evidence", []), db_path)
    counts["ingestions"] = import_ingestion_log(payload.get("ingestion_log", []), db_path)
    return counts

def export_state(db_path="data/monakshi.db") -> dict[str, Any]:
    init_db(db_path)
    with connect(db_path) as con:
        suppliers = [dict(r) for r in con.execute("SELECT * FROM suppliers ORDER BY name")]
        products = [
            dict(r) for r in con.execute(
                """SELECT p.*, s.name supplier_name
                   FROM products p LEFT JOIN suppliers s ON s.id=p.supplier_id
                   ORDER BY p.id"""
            )
        ]
        tasks = [dict(r) for r in con.execute("SELECT * FROM launch_tasks ORDER BY id")]
    return {
        "schema_version": 5,
        "sources": source_registry(db_path),
        "decisions": decision_canon(db_path),
        "suppliers": suppliers,
        "supplier_channels": supplier_channels(db_path),
        "supplier_aliases": supplier_aliases(db_path),
        "products": products,
        "launch_tasks": tasks,
        "evidence": search_evidence(db_path=db_path),
        "ingestion_log": ingestion_log(db_path),
    }
