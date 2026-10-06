#!/usr/bin/env python3
"""Refresh live GitHub metadata for repository-cache/repos.json using stdlib only."""
from __future__ import annotations

import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
CATALOG = ROOT / "repository-cache" / "repos.json"
OUTPUT = ROOT / "repository-cache" / "STATUS.md"
TOKEN = os.environ.get("GITHUB_TOKEN", "")

def fetch(repo: str) -> dict:
    req = urllib.request.Request(
        f"https://api.github.com/repos/{repo}",
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "phoenixmagnum-repository-intelligence-cache",
            **({"Authorization": f"Bearer {TOKEN}"} if TOKEN else {}),
        },
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.load(r)

def main() -> int:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    rows = []
    failures = []
    for item in catalog["repositories"]:
        repo = item["repo"]
        try:
            data = fetch(repo)
            rows.append({
                "repo": repo,
                "priority": item["priority"],
                "category": item["category"],
                "archived": bool(data.get("archived")),
                "stars": int(data.get("stargazers_count") or 0),
                "pushed_at": data.get("pushed_at") or "",
                "default_branch": data.get("default_branch") or "",
                "license": (data.get("license") or {}).get("spdx_id") or "UNKNOWN",
                "url": data.get("html_url") or f"https://github.com/{repo}",
            })
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, json.JSONDecodeError) as exc:
            failures.append((repo, str(exc)))

    priority_order = {"P0": 0, "P1": 1, "P2": 2, "P3": 3}
    rows.sort(key=lambda x: (priority_order.get(x["priority"], 9), x["category"], x["repo"].lower()))

    lines = [
        "# Repository Cache — Live Status",
        "",
        "Generated from the GitHub API. Architectural priority comes from `repos.json`; live metadata does not auto-promote a repository.",
        "",
        "| Priority | Repository | Category | Stars | Archived | Last push | License |",
        "|---|---|---|---:|---|---|---|",
    ]
    for r in rows:
        last_push = r["pushed_at"][:10] if r["pushed_at"] else "unknown"
        lines.append(
            f'| {r["priority"]} | [{r["repo"]}]({r["url"]}) | {r["category"]} | {r["stars"]:,} | '
            f'{"yes" if r["archived"] else "no"} | {last_push} | {r["license"]} |'
        )

    if failures:
        lines.extend(["", "## Refresh failures", ""])
        for repo, err in failures:
            lines.append(f"- `{repo}`: {err}")

    OUTPUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return 0 if not failures else 1

if __name__ == "__main__":
    raise SystemExit(main())
