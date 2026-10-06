from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Iterable

DB_PATH = Path("data/monakshi.db")

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS suppliers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    contact_channel TEXT DEFAULT '',
    status TEXT DEFAULT 'discovered',
    blind_shipping INTEGER DEFAULT 0,
    private_label INTEGER DEFAULT 0,
    mixed_designs INTEGER DEFAULT 0,
    low_moq INTEGER DEFAULT 0,
    no_inventory_model INTEGER DEFAULT 0,
    sample_available INTEGER DEFAULT 0,
    quality_score REAL DEFAULT 0,
    aesthetic_score REAL DEFAULT 0,
    commercial_score REAL DEFAULT 0,
    reliability_score REAL DEFAULT 0,
    source_score REAL,
    source_tier TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS supplier_channels (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER NOT NULL,
    channel_type TEXT NOT NULL,
    handle TEXT DEFAULT '',
    profile_url TEXT DEFAULT '',
    status TEXT DEFAULT 'active',
    is_primary INTEGER DEFAULT 0,
    last_verified_at TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE,
    UNIQUE(supplier_id, channel_type, handle)
);

CREATE INDEX IF NOT EXISTS idx_supplier_channels_supplier
ON supplier_channels(supplier_id);

CREATE TABLE IF NOT EXISTS supplier_aliases (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER NOT NULL,
    alias TEXT NOT NULL,
    alias_type TEXT DEFAULT 'name',
    normalized_alias TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE CASCADE,
    UNIQUE(alias_type, normalized_alias)
);

CREATE INDEX IF NOT EXISTS idx_supplier_aliases_supplier
ON supplier_aliases(supplier_id);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    supplier_id INTEGER,
    name TEXT NOT NULL,
    category TEXT DEFAULT '',
    supplier_price REAL,
    target_retail REAL,
    shipping_cost REAL DEFAULT 0,
    packaging_cost REAL DEFAULT 0,
    payment_fee_pct REAL DEFAULT 2.0,
    sample_status TEXT DEFAULT 'not_requested',
    burn_test_pass INTEGER DEFAULT 0,
    packaging_test_pass INTEGER DEFAULT 0,
    photo_approved INTEGER DEFAULT 0,
    specs_verified INTEGER DEFAULT 0,
    launch_status TEXT DEFAULT 'candidate',
    notes TEXT DEFAULT '',
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id) ON DELETE SET NULL
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_products_supplier_name
ON products(supplier_id, name);

CREATE TABLE IF NOT EXISTS documents (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_name TEXT NOT NULL,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS watches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    label TEXT NOT NULL,
    url TEXT NOT NULL UNIQUE,
    last_hash TEXT,
    last_title TEXT,
    last_excerpt TEXT,
    last_checked_at TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS watch_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    watch_id INTEGER NOT NULL,
    change_type TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (watch_id) REFERENCES watches(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS evidence_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT UNIQUE,
    entity_type TEXT NOT NULL,
    entity_name TEXT NOT NULL,
    source_type TEXT NOT NULL,
    source_label TEXT DEFAULT '',
    source_ref TEXT DEFAULT '',
    occurred_at TEXT DEFAULT '',
    subject TEXT DEFAULT '',
    summary TEXT NOT NULL,
    facts_json TEXT DEFAULT '{}',
    decision_impact TEXT DEFAULT '',
    confidence TEXT DEFAULT 'direct',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_evidence_entity
ON evidence_records(entity_type, entity_name);

CREATE TABLE IF NOT EXISTS ingestion_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    external_id TEXT NOT NULL UNIQUE,
    source_system TEXT NOT NULL,
    entity_name TEXT DEFAULT '',
    artifact_type TEXT DEFAULT 'record',
    content_sha256 TEXT DEFAULT '',
    source_ref_sha256 TEXT DEFAULT '',
    redacted_label TEXT DEFAULT '',
    occurred_at TEXT DEFAULT '',
    status TEXT DEFAULT 'imported',
    notes TEXT DEFAULT '',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_ingestion_log_hash
ON ingestion_log(source_system, entity_name, content_sha256);

CREATE TABLE IF NOT EXISTS source_registry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT NOT NULL UNIQUE,
    name TEXT NOT NULL,
    source_type TEXT DEFAULT 'other',
    authority_rank INTEGER NOT NULL DEFAULT 8,
    version TEXT DEFAULT '',
    location TEXT DEFAULT '',
    is_controlling INTEGER DEFAULT 0,
    last_verified_at TEXT DEFAULT '',
    freshness_days INTEGER DEFAULT 30,
    status TEXT DEFAULT 'active',
    notes TEXT DEFAULT '',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_source_registry_authority
ON source_registry(authority_rank, is_controlling);

CREATE TABLE IF NOT EXISTS decision_canon (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    decision_id TEXT NOT NULL UNIQUE,
    domain TEXT DEFAULT 'general',
    decision_key TEXT NOT NULL,
    decision_value TEXT NOT NULL,
    status TEXT DEFAULT 'working',
    source_id TEXT,
    effective_date TEXT DEFAULT '',
    rationale TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (source_id) REFERENCES source_registry(source_id) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_decision_canon_key
ON decision_canon(decision_key, status);

CREATE TABLE IF NOT EXISTS launch_tasks (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    source_id TEXT,
    area TEXT NOT NULL,
    task TEXT NOT NULL,
    status TEXT DEFAULT 'todo',
    blocker TEXT DEFAULT '',
    owner TEXT DEFAULT 'Founder',
    priority TEXT DEFAULT '',
    due_gate TEXT DEFAULT '',
    dependency TEXT DEFAULT '',
    next_action TEXT DEFAULT '',
    evidence TEXT DEFAULT '',
    notes TEXT DEFAULT '',
    UNIQUE(area, task)
);

CREATE UNIQUE INDEX IF NOT EXISTS idx_launch_tasks_source_id
ON launch_tasks(source_id) WHERE source_id IS NOT NULL;
"""

DEFAULT_TASKS = [
    ("Storefront", "Upgrade/publish Wix site when launch-ready"),
    ("Payments", "Complete native Wix payment setup and live checkout rehearsal"),
    ("Products", "Replace placeholders with verified launch SKUs"),
    ("Products", "Approve samples, burn tests, packaging tests and product photography"),
    ("Suppliers", "Lock supplier agreement and fulfilment annexure for launch suppliers"),
    ("Fulfilment", "Verify blind-shipping packout and tracking workflow"),
    ("Legal", "Finalize legal identity, policies, GST decision and trademark work"),
    ("Marketing", "Publish first Instagram grid and 10-day pre-launch sequence"),
    ("Analytics", "Confirm launch analytics and conversion tracking"),
]

SUPPLIER_MIGRATIONS = {
    "source_score": "REAL",
    "source_tier": "TEXT DEFAULT ''",
}

TASK_MIGRATIONS = {
    "source_id": "TEXT",
    "priority": "TEXT DEFAULT ''",
    "due_gate": "TEXT DEFAULT ''",
    "dependency": "TEXT DEFAULT ''",
    "next_action": "TEXT DEFAULT ''",
    "evidence": "TEXT DEFAULT ''",
    "notes": "TEXT DEFAULT ''",
}

def connect(path: Path | str = DB_PATH) -> sqlite3.Connection:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    con.execute("PRAGMA foreign_keys = ON")
    return con

def _ensure_columns(con: sqlite3.Connection, table: str, columns: dict[str, str]) -> None:
    existing = {row["name"] for row in con.execute(f"PRAGMA table_info({table})").fetchall()}
    for name, sql_type in columns.items():
        if name not in existing:
            con.execute(f"ALTER TABLE {table} ADD COLUMN {name} {sql_type}")

def init_db(path: Path | str = DB_PATH) -> None:
    with connect(path) as con:
        con.executescript(SCHEMA)
        _ensure_columns(con, "suppliers", SUPPLIER_MIGRATIONS)
        _ensure_columns(con, "launch_tasks", TASK_MIGRATIONS)
        con.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_launch_tasks_source_id "
            "ON launch_tasks(source_id) WHERE source_id IS NOT NULL"
        )
        con.executemany(
            "INSERT OR IGNORE INTO launch_tasks(area, task) VALUES (?, ?)", DEFAULT_TASKS
        )

def rows(query: str, params: Iterable = (), path: Path | str = DB_PATH):
    with connect(path) as con:
        return [dict(r) for r in con.execute(query, tuple(params)).fetchall()]
