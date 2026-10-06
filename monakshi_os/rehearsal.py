from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any

from .db import rows
from .scoring import launch_gate

HARD_TASK_GATES = {
    "L01": "Legal structure / invoicing identity",
    "L02": "GST / interstate tax position",
    "S08": "Supplier agreement + blind-fulfilment annexure",
    "B03": "Legal retail label content",
    "W02": "Shipping / returns / refund / cancellation policies",
    "W03": "Privacy / terms / consumer-care",
    "W04": "Native Wix + Razorpay live payment path",
    "O01": "Courier choice and real shipping slabs",
    "O02": "Returns / damage responsibility matrix",
    "Q04": "Blind-shipping secret-shop test",
}

@dataclass(frozen=True)
class GateResult:
    key: str
    label: str
    passed: bool
    detail: str

def _task_map(db_path="data/monakshi.db") -> dict[str, dict[str, Any]]:
    return {
        row["source_id"]: row
        for row in rows(
            "SELECT * FROM launch_tasks WHERE source_id IS NOT NULL",
            path=db_path,
        )
    }

def evaluate_launch(db_path="data/monakshi.db") -> dict[str, Any]:
    task_map = _task_map(db_path)
    gates: list[GateResult] = []

    for source_id, label in HARD_TASK_GATES.items():
        task = task_map.get(source_id)
        passed = bool(task and task.get("status") == "done")
        if not task:
            detail = "Missing from launch tracker"
        elif passed:
            detail = "Completed"
        else:
            detail = f"Status: {task.get('status') or 'unknown'}"
            if task.get("blocker"):
                detail += f" | blocker: {task['blocker']}"
        gates.append(GateResult(source_id, label, passed, detail))

    products = rows("SELECT * FROM products ORDER BY id", path=db_path)
    ready = []
    product_failures = []
    for product in products:
        passed, missing = launch_gate(product)
        if passed:
            ready.append(product["name"])
        else:
            product_failures.append({
                "name": product["name"],
                "missing": missing,
            })

    product_gate = GateResult(
        "SKU",
        "At least one fully qualified launch SKU",
        bool(ready),
        f"{len(ready)} launch-ready SKU(s)" if ready else "No SKU has cleared sample, burn, packaging, imagery, specs and margin gates",
    )
    gates.append(product_gate)

    passed = all(g.passed for g in gates)
    blocking = [asdict(g) for g in gates if not g.passed]

    return {
        "decision": "GO" if passed else "NO-GO",
        "passed": passed,
        "gates": [asdict(g) for g in gates],
        "blocking_gates": blocking,
        "launch_ready_skus": ready,
        "product_failures": product_failures,
    }

def render_markdown(report: dict[str, Any]) -> str:
    lines = [
        "# House of Monakshi Launch Rehearsal",
        "",
        f"## Decision: {report['decision']}",
        "",
    ]
    if report["blocking_gates"]:
        lines += ["### Blocking gates", ""]
        for gate in report["blocking_gates"]:
            lines.append(f"- **{gate['key']} · {gate['label']}**: {gate['detail']}")
        lines.append("")
    else:
        lines += ["All hard launch gates cleared.", ""]

    lines += [
        "### Launch-ready SKUs",
        "",
    ]
    if report["launch_ready_skus"]:
        lines.extend(f"- {name}" for name in report["launch_ready_skus"])
    else:
        lines.append("- None")

    lines += [
        "",
        "### Rule",
        "",
        "A GO decision requires every hard operating gate above and at least one fully qualified SKU. "
        "Marketing urgency, festive timing or visual polish cannot override a failed gate.",
        "",
    ]
    return "\n".join(lines)
