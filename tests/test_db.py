from pathlib import Path

from monakshi_os.db import init_db, rows


def test_init_db_creates_launch_gates(tmp_path: Path):
    db = tmp_path / "monakshi.db"
    init_db(db)
    tasks = rows("SELECT * FROM launch_tasks", path=db)
    assert len(tasks) >= 8
    assert any(t["area"] == "Products" for t in tasks)
