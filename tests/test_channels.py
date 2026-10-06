from pathlib import Path

from monakshi_os.channels import (
    add_alias,
    add_channel,
    channel_is_stale,
    resolve_supplier,
    supplier_channels,
)
from monakshi_os.db import connect, init_db


def test_alias_and_multichannel_identity(tmp_path: Path):
    db = tmp_path / "monakshi.db"
    init_db(db)
    with connect(db) as con:
        con.execute("INSERT INTO suppliers(name) VALUES ('Studio Example')")
        supplier_id = con.execute("SELECT id FROM suppliers WHERE name='Studio Example'").fetchone()["id"]

    add_alias(supplier_id, "@studio_example", "instagram", db)
    add_alias(supplier_id, "+91 99999 11111", "whatsapp", db)
    add_channel(supplier_id, "instagram", "@studio_example", "https://instagram.com/studio_example", last_verified_at="2026-10-06", db_path=db)
    add_channel(supplier_id, "whatsapp", "+91 99999 11111", is_primary=True, last_verified_at="2026-10-06", db_path=db)

    assert resolve_supplier("@studio_example", "instagram", db)["name"] == "Studio Example"
    assert resolve_supplier("+91 99999 11111", "whatsapp", db)["name"] == "Studio Example"
    assert len(supplier_channels(db)) == 2


def test_stale_channel_detection():
    assert channel_is_stale("") is True
    assert channel_is_stale("2020-01-01") is True
    assert channel_is_stale("2999-01-01") is False
