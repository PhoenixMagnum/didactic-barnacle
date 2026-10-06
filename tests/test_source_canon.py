from datetime import datetime, timezone
from pathlib import Path

from openpyxl import Workbook

from monakshi_os.command_centre import import_command_centre
from monakshi_os.db import rows
from monakshi_os.source_canon import (
    decision_conflicts,
    resolve_current_decision,
    source_is_stale,
    upsert_decision,
    upsert_source,
)


def test_authority_resolves_current_decision(tmp_path: Path):
    db = tmp_path / "monakshi.db"
    upsert_source({"source_id": "cc", "name": "CC", "authority_rank": 2, "last_verified_at": "2026-10-06"}, db)
    upsert_source({"source_id": "founder", "name": "Founder", "authority_rank": 1, "last_verified_at": "2026-10-06"}, db)
    upsert_decision({"decision_id": "d1", "decision_key": "gateway", "decision_value": "Razorpay", "status": "working", "source_id": "cc"}, db)
    upsert_decision({"decision_id": "d2", "decision_key": "gateway", "decision_value": "Other", "status": "locked", "source_id": "founder"}, db)

    assert resolve_current_decision("gateway", db)["decision_value"] == "Other"
    assert len(decision_conflicts(db)) == 1


def test_source_freshness():
    assert source_is_stale({"last_verified_at": "", "freshness_days": 30}) is True
    assert source_is_stale(
        {"last_verified_at": "2026-10-06", "freshness_days": 30},
        now=datetime(2026, 10, 7, tzinfo=timezone.utc),
    ) is False


def test_command_centre_import(tmp_path: Path):
    db = tmp_path / "monakshi.db"
    wb = Workbook()
    ws = wb.active
    ws.title = "Master Tasks"
    ws.append(["ID","Track","Task","Owner","Priority","Status","Due / Gate","Dependency","Next Action","Evidence / Output","Source / URL","Notes"])
    ws.append(["S01","Suppliers","Launch Five locked: Alpha, Beta, Gamma, Delta, Epsilon","Assistant","Critical","Completed","Done","","Use five","Board","",""])
    ws.append(["L01","Legal & Finance","Choose launch legal structure","Founder","Critical","In Progress","Before sale","CA","Use sole-prop as working assumption","Note","",""])
    ws.append(["Q05","Quality","Final SKU scoring","Assistant","Critical","In Progress","After tests","","Score","Race","","Target soft-launch shelf: 6–10 genuinely qualified SKUs."])
    dash = wb.create_sheet("Dashboard")
    dash.append(["Launch status","PRE-LAUNCH EXECUTION"])
    dash.append(["Target model","Low inventory / supplier-held or blind D2C"])
    dash.append(["Primary gateway","Razorpay"])
    dash.append(["Backup gateway","Cashfree · deferred"])

    path = tmp_path / "House_of_Monakshi_Launch_Command_Centre_v13.xlsx"
    wb.save(path)

    result = import_command_centre(path.read_bytes(), path.name, str(db))
    assert result["tasks"] == 3
    assert result["version"] == "v13"
    assert len(rows("SELECT * FROM launch_tasks", path=db)) >= 3
    assert resolve_current_decision("primary_gateway", str(db))["decision_value"] == "Razorpay"
    assert "Alpha" in resolve_current_decision("launch_suppliers", str(db))["decision_value"]
