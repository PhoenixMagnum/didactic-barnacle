from __future__ import annotations

from monakshi_os.db import rows
from monakshi_os.scout import check_watch


def main():
    watches = rows("SELECT id, label, url FROM watches ORDER BY id")
    if not watches:
        print("No watchlist URLs configured.")
        return

    for watch in watches:
        try:
            result = check_watch(watch["id"])
            marker = "CHANGED" if result["changed"] else "ok"
            print(f"[{marker}] {watch['label']} :: {watch['url']}")
        except Exception as exc:
            print(f"[error] {watch['label']} :: {exc}")


if __name__ == "__main__":
    main()
