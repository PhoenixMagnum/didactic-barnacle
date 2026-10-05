from __future__ import annotations

from monakshi_os.db import init_db, rows
from monakshi_os.scoring import launch_gate, supplier_score


def main():
    init_db()
    tasks = rows(
        """SELECT * FROM launch_tasks
           WHERE status != 'done'
           ORDER BY
             CASE priority WHEN 'Critical' THEN 0 WHEN 'High' THEN 1 ELSE 2 END,
             id"""
    )
    suppliers = rows("SELECT * FROM suppliers ORDER BY source_score DESC, name")
    products = rows("SELECT * FROM products ORDER BY id")

    print("HOUSE OF MONAKSHI :: DAILY BRIEF")
    print("=" * 36)

    critical = [t for t in tasks if t.get("priority") == "Critical"]
    print(f"Open critical tasks: {len(critical)}")
    for t in critical[:12]:
        source = f"{t.get('source_id')} · " if t.get("source_id") else ""
        blocker = f" | blocker: {t['blocker']}" if t.get("blocker") else ""
        print(f"- {source}{t['task']} [{t['status']}]{blocker}")

    print("\nSupplier front-runners:")
    for s in suppliers[:8]:
        computed = supplier_score(s)
        imported = f"source {s['source_score']}/100" if s.get("source_score") is not None else f"computed {computed.score}/100"
        print(f"- {s['name']}: {imported} · {s.get('status','')}")

    ready = []
    for p in products:
        passed, _ = launch_gate(p)
        if passed:
            ready.append(p)
    print(f"\nLaunch-ready SKUs: {len(ready)} / {len(products)}")
    for p in ready:
        print(f"- {p['name']}")


if __name__ == "__main__":
    main()
