from __future__ import annotations

import argparse

from monakshi_os.state_io import import_state, load_payload


def main():
    parser = argparse.ArgumentParser(description="Load a private House of Monakshi state JSON into the local database.")
    parser.add_argument("json_path")
    parser.add_argument("--db", default="data/monakshi.db")
    args = parser.parse_args()

    counts = import_state(load_payload(args.json_path), args.db)
    print(
        f"Imported {counts['launch_tasks']} tasks, "
        f"{counts['suppliers']} suppliers, {counts['products']} products."
    )


if __name__ == "__main__":
    main()
