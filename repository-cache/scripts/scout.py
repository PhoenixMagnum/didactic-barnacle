#!/usr/bin/env python3
"""Just-in-time GitHub repository scout.

Reads repository-cache/needs.json, searches GitHub, excludes repos already in
repos.json, scores candidate health, and writes CANDIDATES.md.

Environment overrides:
  SCOUT_QUERY: run one ad-hoc GitHub repository search instead of needs.json
  SCOUT_STACK: stack id for the ad-hoc search, default S6
  GITHUB_TOKEN: optional but strongly recommended
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import pathlib
import re
import urllib.parse
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[2]
CACHE = ROOT / "repository-cache"
NEEDS = CACHE / "needs.json"
CATALOG = CACHE / "repos.json"
OUTPUT = CACHE / "CANDIDATES.md"
TOKEN = os.environ.get("GITHUB_TOKEN", "")
ADHOC_QUERY = os.environ.get("SCOUT_QUERY", "").strip()
ADHOC_STACK = os.environ.get("SCOUT_STACK", "S6").strip() or "S6"

def api_json(url: str) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "phoenixmagnum-repository-scout",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    req = urllib.request.Request(url, headers=headers)
    with urllib.request.urlopen(req, timeout=45) as resp:
        return json.load(resp)

def search(query: str, limit: int) -> list[dict]:
    params = urllib.parse.urlencode({
        "q": query,
        "sort": "stars",
        "order": "desc",
        "per_page": min(max(limit, 1), 25),
    })
    return api_json(f"https://api.github.com/search/repositories?{params}").get("items", [])

def age_days(iso: str | None) -> int:
    if not iso:
        return 99999
    when = dt.datetime.fromisoformat(iso.replace("Z", "+00:00"))
    now = dt.datetime.now(dt.timezone.utc)
    return max(0, (now - when).days)

def health_score(repo: dict, rank: int) -> int:
    if repo.get("archived"):
        return 0

    stars = int(repo.get("stargazers_count") or 0)
    forks = int(repo.get("forks_count") or 0)
    days = age_days(repo.get("pushed_at"))
    license_ok = bool((repo.get("license") or {}).get("spdx_id"))

    star_score = min(35, round(math.log10(max(stars, 1)) * 9))
    fork_score = min(10, round(math.log10(max(forks, 1)) * 3))
    if days <= 30:
        fresh_score = 30
    elif days <= 90:
        fresh_score = 26
    elif days <= 180:
        fresh_score = 21
    elif days <= 365:
        fresh_score = 15
    elif days <= 730:
        fresh_score = 8
    else:
        fresh_score = 2

    license_score = 10 if license_ok else 2
    rank_score = max(0, 15 - rank * 2)
    fork_penalty = 12 if repo.get("fork") else 0
    return max(0, min(100, star_score + fork_score + fresh_score + license_score + rank_score - fork_penalty))

def safe_text(value: str | None) -> str:
    return (value or "").replace("|", "\\|").replace("\n", " ").strip()

def main() -> None:
    existing = {
        x["repo"].lower()
        for x in json.loads(CATALOG.read_text(encoding="utf-8"))["repositories"]
    }

    if ADHOC_QUERY:
        searches = [{"id": "ad-hoc", "stack": ADHOC_STACK, "query": ADHOC_QUERY, "limit": 12}]
        mode = "ad-hoc"
    else:
        searches = json.loads(NEEDS.read_text(encoding="utf-8"))["needs"]
        mode = "scheduled"

    sections = []
    for need in searches:
        raw = search(need["query"], int(need.get("limit", 8)))
        candidates = []
        for rank, item in enumerate(raw):
            full_name = (item.get("full_name") or "").strip()
            if not full_name or full_name.lower() in existing or item.get("archived"):
                continue
            candidates.append({
                "repo": full_name,
                "url": item.get("html_url") or f"https://github.com/{full_name}",
                "description": safe_text(item.get("description")),
                "stars": int(item.get("stargazers_count") or 0),
                "pushed": (item.get("pushed_at") or "")[:10],
                "license": (item.get("license") or {}).get("spdx_id") or "UNKNOWN",
                "score": health_score(item, rank),
            })
        candidates.sort(key=lambda x: (-x["score"], -x["stars"], x["repo"].lower()))
        sections.append((need, candidates[:8]))

    stamp = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        "# Repository Scout — Candidate Queue",
        "",
        f"Generated {stamp} in **{mode}** mode.",
        "",
        "This file is a discovery queue, not an install manifest. Candidates must pass stack fit, license/security review, duplication checks and a concrete use-case gate before adoption.",
        "",
    ]

    for need, candidates in sections:
        lines += [
            f'## {need["id"]} · {need["stack"]}',
            "",
            f'GitHub query: `{need["query"]}`',
            "",
        ]
        if not candidates:
            lines += ["No uncached candidates surfaced.", ""]
            continue
        lines += [
            "| Score | Repository | Stars | Last push | License | Why it surfaced |",
            "|---:|---|---:|---|---|---|",
        ]
        for c in candidates:
            lines.append(
                f'| {c["score"]} | [{c["repo"]}]({c["url"]}) | {c["stars"]:,} | '
                f'{c["pushed"] or "unknown"} | {c["license"]} | {c["description"][:180]} |'
            )
        lines.append("")

    OUTPUT.write_text("\n".join(lines), encoding="utf-8")

if __name__ == "__main__":
    main()
