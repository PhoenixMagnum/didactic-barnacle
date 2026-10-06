from __future__ import annotations

import argparse
import json
from pathlib import Path

from monakshi_os.evidence import import_evidence


def main():
    parser = argparse.ArgumentParser(
        description="Import structured private evidence into the local House of Monakshi evidence ledger."
    )
    parser.add_argument("json_path", help="JSON file containing an evidence array or a full private-state object.")
    parser.add_argument("--db", default="data/monakshi.db")
    args = parser.parse_args()

    payload = json.loads(Path(args.json_path).read_text(encoding="utf-8"))
    records = payload.get("evidence", payload) if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise SystemExit("Expected a JSON list of evidence records or an object containing an 'evidence' list.")

    count = import_evidence(records, args.db)
    print(f"Imported {count} evidence records.")


if __name__ == "__main__":
    main()
