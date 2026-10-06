from pathlib import Path

from monakshi_os.db import connect, init_db
from monakshi_os.rehearsal import evaluate_launch


def test_launch_report_defaults_to_no_go(tmp_path: Path):
    db = tmp_path / "monakshi.db"
    init_db(db)
    report = evaluate_launch(db)
    assert report["decision"] == "NO-GO"
    keys = {g["key"] for g in report["blocking_gates"]}
    assert "W04" in keys
    assert "SKU" in keys


def test_launch_go_requires_all_hard_tasks_and_one_qualified_sku(tmp_path: Path):
    db = tmp_path / "monakshi.db"
    init_db(db)

    required = ["L01", "L02", "S08", "B03", "W02", "W03", "W04", "O01", "O02", "Q04"]
    with connect(db) as con:
        for source_id in required:
            con.execute(
                """INSERT INTO launch_tasks(source_id, area, task, status)
                   VALUES (?, 'Test', ?, 'done')""",
                (source_id, source_id),
            )
        con.execute(
            """INSERT INTO products(
                name, supplier_price, target_retail, shipping_cost, packaging_cost,
                payment_fee_pct, sample_status, burn_test_pass, packaging_test_pass,
                photo_approved, specs_verified
            ) VALUES ('Qualified SKU', 100, 400, 40, 20, 2, 'approved', 1, 1, 1, 1)"""
        )

    report = evaluate_launch(db)
    assert report["decision"] == "GO"
    assert report["launch_ready_skus"] == ["Qualified SKU"]
