#!/usr/bin/env python3
"""Resume bulk-add after a crash/restart.

Reads /admin/sources for live chunk_count, then:
- Skips REINGEST_IDS that already have chunks > 0
- Skips ALL_NEW whose URL is already in the manifest with chunks > 0

Sequential, polls each job, won't bail on individual failures.

Usage on the server (so HTTP loss survives ssh disconnect):
    BBRAIN_TOKEN=$(grep ^ADMIN_TOKEN /opt/basketball-brain/api/.env | cut -d= -f2) \\
    BBRAIN_API=http://localhost:8000 \\
    nohup python3 /opt/basketball-brain/scripts/bulk_resume.py \\
        > /opt/basketball-brain/bulk_resume.log 2>&1 &
"""
from __future__ import annotations

import os
import sys

# Reuse data + helpers from the original bulk_add_corpus script.
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)
from bulk_add_corpus import (  # noqa: E402
    ALL_NEW,
    REINGEST_IDS,
    add_url,
    get_json,
    reingest,
)


def main() -> None:
    print("=" * 60)
    print("BULK RESUME — fetching live source list")
    print("=" * 60)

    sources = get_json("/admin/sources").get("sources", [])
    by_id = {s["id"]: s for s in sources}
    by_url = {s.get("url"): s for s in sources if s.get("url")}

    # Filter REINGEST_IDS — only re-do ones that have 0 chunks
    todo_reingest = []
    for sid in REINGEST_IDS:
        s = by_id.get(sid)
        if s and s.get("chunk_count", 0) > 0:
            print(f"  skip reingest (chunks={s['chunk_count']}): {sid}")
            continue
        todo_reingest.append(sid)

    # Filter ALL_NEW — skip URLs already ingested with chunks > 0
    todo_new = []
    for spec in ALL_NEW:
        s = by_url.get(spec["url"])
        if s and s.get("chunk_count", 0) > 0:
            print(f"  skip url (chunks={s['chunk_count']}): {spec['title'][:60]}")
            continue
        todo_new.append(spec)

    total = len(todo_reingest) + len(todo_new)
    print()
    print(f"To do: {len(todo_reingest)} reingests + {len(todo_new)} new = {total} ops")
    print("=" * 60)

    results: list[tuple[str, str, str]] = []

    for sid in todo_reingest:
        status, info = reingest(sid)
        results.append(("reingest", sid, f"{status}: {info}"))

    for spec in todo_new:
        status, info = add_url(spec)
        results.append(("new", spec["title"], f"{status}: {info}"))

    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    ok = sum(1 for _, _, s in results if s.startswith("done"))
    failed = [(k, label, s) for k, label, s in results if not s.startswith("done")]
    print(f"OK:     {ok}/{len(results)}")
    print(f"Failed: {len(failed)}")
    for kind, label, status in failed:
        print(f"  [{kind}] {label[:60]:60} → {status[:120]}")


if __name__ == "__main__":
    main()
