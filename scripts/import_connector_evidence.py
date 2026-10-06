from __future__ import annotations

import argparse
import json
from pathlib import Path

from monakshi_os.ingestion import ingest_connector_records


def main():
    parser = argparse.ArgumentParser(
        description="Import explicitly selected Gmail/Drive evidence into local Monakshi OS."
    )
    parser.add_argument("json_path", help="Private JSON containing a records list.")
    parser.add_argument("--db", default="data/monakshi.db")
    args = parser.parse_args()

    payload = json.loads(Path(args.json_path).read_text(encoding="utf-8"))
    records = payload.get("records", payload) if isinstance(payload, dict) else payload
    if not isinstance(records, list):
        raise SystemExit("Expected a JSON list or an object containing a 'records' list.")

    result = ingest_connector_records(records, args.db)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
