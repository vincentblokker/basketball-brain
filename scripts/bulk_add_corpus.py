#!/usr/bin/env python3
"""Bulk-add the full content batch (NL/BE + Jr. NBA + BE) and reingest existing PDFs.

Sequential, with per-job polling and clean error-reporting. Designed to run
overnight on the ARM server. Failures don't bail — logs and moves on.

Usage:
    BBRAIN_TOKEN=$(grep ^ADMIN_TOKEN /opt/basketball-brain/api/.env | cut -d= -f2)
    BBRAIN_API=https://brain.clubduty.app/api  (default)
    python scripts/bulk_add_corpus.py
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request

API = os.environ.get("BBRAIN_API", "https://brain.clubduty.app/api").rstrip("/")
TOKEN = os.environ.get("BBRAIN_TOKEN", "").strip()
if not TOKEN:
    print("ERROR: BBRAIN_TOKEN not set", file=sys.stderr)
    sys.exit(1)

HEADERS = {"Authorization": f"Bearer {TOKEN}"}


# ---------- source definitions ----------

# Existing PDFs that need reingest (page-aware chunker → page numbers in chunks)
REINGEST_IDS = [
    "fiba-official-basketball-rules-2024",
    "fiba-official-interpretations-2024-obri",
    "fiba-wabc-mini-basketball-coaches-manual",
    "fiba-wabc-coaching-course-manual-level-1",
    "fiba-wabc-coaching-course-manual-level-2",
    "usa-basketball-youth-development-guidebook",
]

# 13 NL/BE bronnen
NL_BE_SOURCES = [
    # NBB
    {
        "url": "https://basketball.nl/app/uploads/2026/03/Handboek-Trainers-en-Coaches-seizoen-2026-2027-def.pdf",
        "title": "NBB Handboek Trainers en Coaches 2026-2027",
        "content_type": "philosophy", "audience": ["coach"],
        "age_category": "all", "language": "nl",
        "authority": "official", "level": "n/a", "topic": "coaching-philosophy",
        "region": "NL", "ruleset": "FIBA", "chunk_type": "prose",
    },
    {
        "url": "https://basketball.nl/app/uploads/2026/03/Wedstrijdreglement-2026-2027-definitieve-versie-2026-03-31.pdf",
        "title": "NBB Wedstrijdreglement 2026-2027",
        "content_type": "rule", "audience": ["coach", "referee"],
        "age_category": "all", "language": "nl",
        "authority": "official", "level": "n/a", "topic": None,
        "region": "NL", "ruleset": "FIBA", "chunk_type": "prose",
    },
    {
        "url": "https://basketball.nl/app/uploads/2026/01/Handboek-Competities-2025-2026_versie-060126.pdf",
        "title": "NBB Handboek Competities 2025-2026",
        "content_type": "rule", "audience": ["coach", "referee"],
        "age_category": "all", "language": "nl",
        "authority": "official", "level": "n/a", "topic": None,
        "region": "NL", "ruleset": "FIBA", "chunk_type": "prose",
    },
    {
        "url": "https://basketball.nl/app/uploads/2026/03/Handboek-arbitrage-seizoen-2026-2027.pdf",
        "title": "NBB Handboek Arbitrage 2026-2027",
        "content_type": "rule", "audience": ["referee"],
        "age_category": "all", "language": "nl",
        "authority": "official", "level": "n/a", "topic": None,
        "region": "NL", "ruleset": "FIBA", "chunk_type": "prose",
    },
    {
        "url": "https://basketball.nl/app/uploads/2025/09/Handboek-Versneld-innemen-van-de-bal-2025-2026.pdf",
        "title": "NBB Handboek Versneld Innemen van de Bal 2025-2026",
        "content_type": "rule", "audience": ["coach", "referee"],
        "age_category": "U10,U12,U14", "language": "nl",
        "authority": "official", "level": "n/a", "topic": None,
        "region": "NL", "ruleset": "FIBA", "chunk_type": "prose",
    },

    # Basketball Vlaanderen
    {
        "url": "https://www.basketbal.vlaanderen/documenten/Jeugdco%C3%B6rdinator/Basketbal-Vlaanderen-Leerlijn.pdf",
        "title": "Basketbal Vlaanderen — Leerlijn (overzicht)",
        "content_type": "philosophy", "audience": ["coach"],
        "age_category": "U10,U12,U14,U16,U18", "language": "nl",
        "authority": "official", "level": "n/a", "topic": "talent-development",
        "region": "EU", "ruleset": "FIBA", "chunk_type": "prose",
    },
    {
        "url": "https://www.basketbal.vlaanderen/documenten/Jeugdco%C3%B6rdinator/Leerlijn-Basketbal-Vlaanderen-niveau-1-en-2.pdf",
        "title": "Basketbal Vlaanderen — Leerlijn niveau 1 en 2",
        "content_type": "philosophy", "audience": ["coach"],
        "age_category": "U10,U12", "language": "nl",
        "authority": "official", "level": "L1", "topic": "talent-development",
        "region": "EU", "ruleset": "FIBA", "chunk_type": "prose",
    },
    {
        "url": "https://www.basketbal.vlaanderen/documenten/Jeugdco%C3%B6rdinator/Leerlijn-Basketbal-Vlaanderen-niveau-3.pdf",
        "title": "Basketbal Vlaanderen — Leerlijn niveau 3",
        "content_type": "philosophy", "audience": ["coach"],
        "age_category": "U14,U16", "language": "nl",
        "authority": "official", "level": "L2", "topic": "talent-development",
        "region": "EU", "ruleset": "FIBA", "chunk_type": "prose",
    },
    {
        "url": "https://www.basketbal.vlaanderen/documenten/Jeugdco%C3%B6rdinator/Leerlijn-Basketbal-Vlaanderen-niveau-4.pdf",
        "title": "Basketbal Vlaanderen — Leerlijn niveau 4",
        "content_type": "philosophy", "audience": ["coach"],
        "age_category": "U16,U18", "language": "nl",
        "authority": "official", "level": "L3", "topic": "talent-development",
        "region": "EU", "ruleset": "FIBA", "chunk_type": "prose",
    },
    {
        "url": "https://www.basketbal.vlaanderen/documenten/Jeugdco%C3%B6rdinator/Opleiding-beginnende-jeugdco%C3%B6rdinator.pdf",
        "title": "Basketbal Vlaanderen — Opleiding beginnende jeugdcoördinator",
        "content_type": "philosophy", "audience": ["coach"],
        "age_category": "all", "language": "nl",
        "authority": "official", "level": "n/a", "topic": "coaching-philosophy",
        "region": "EU", "ruleset": "FIBA", "chunk_type": "prose",
    },
    {
        "url": "https://www.basketbal.vlaanderen/documenten/Give-Go/Leidraad-voor-clubs-sportieve-werking-2025-2026.pdf",
        "title": "Basketbal Vlaanderen — Give & Go Leidraad sportieve werking 2025-2026",
        "content_type": "philosophy", "audience": ["coach"],
        "age_category": "all", "language": "nl",
        "authority": "official", "level": "n/a", "topic": "coaching-philosophy",
        "region": "EU", "ruleset": "FIBA", "chunk_type": "prose",
    },
    {
        "url": "https://www.basketbal.vlaanderen/documenten/Give-Go/Reglement-Give-Go-2026.pdf",
        "title": "Basketbal Vlaanderen — Reglement Give & Go 2026",
        "content_type": "rule", "audience": ["coach"],
        "age_category": "all", "language": "nl",
        "authority": "official", "level": "n/a", "topic": None,
        "region": "EU", "ruleset": "FIBA", "chunk_type": "prose",
    },
    {
        "url": "https://www.basketbal.vlaanderen/documenten/Jeugdco%C3%B6rdinator/Presentatie-Club-Time-out-Hoe-verbeter-ik-mijn-jeugdwerking-met-ondersteuning-van-Basketbal-Vlaanderen.pdf",
        "title": "Basketbal Vlaanderen — Hoe verbeter ik mijn jeugdwerking",
        "content_type": "philosophy", "audience": ["coach"],
        "age_category": "all", "language": "nl",
        "authority": "official", "level": "n/a", "topic": "coaching-philosophy",
        "region": "EU", "ruleset": "FIBA", "chunk_type": "prose",
    },
]

# 26 Jr. NBA practice plans
def _jrnba_starter() -> list[dict]:
    base = "https://ak-static.cms.nba.com/wp-content/uploads/sites/52"
    items = [
        ("starter-intro", f"{base}/2016/09/JrNBA_Starter_Intro.pdf",
         "Jr. NBA Starter — Intro"),
    ]
    months = {"01": "09", "02": "10", "03": "12", "04": "12", "05": "12",
              "06": "12", "07": "12", "08": "12", "09": "12", "10": "12",
              "11": "12", "12": "12"}
    for nn in range(1, 13):
        n = f"{nn:02d}"
        m = months[n]
        items.append((
            f"starter-pp-{n}",
            f"{base}/2016/{m}/JrNBA17_Curriculum_Starter_PP_{n}.pdf",
            f"Jr. NBA Starter — Practice Plan {n}",
        ))
    return [
        {
            "url": url,
            "title": title,
            "content_type": "philosophy", "audience": ["coach"],
            "age_category": "U10", "language": "en",
            "authority": "official", "level": "Starter",
            "topic": "practice-plan", "region": "USA",
            "ruleset": "NBA", "chunk_type": "prose",
        }
        for _slug, url, title in items
    ]

def _jrnba_rookie() -> list[dict]:
    base = "https://ak-static.cms.nba.com/wp-content/uploads/sites/52"
    items = [(
        "rookie-intro",
        f"{base}/2023/04/JrNBA22_Curriculum_Rookie_Intro.pdf",
        "Jr. NBA Rookie — Intro",
    )]
    months = {"01": "09", "02": "09", "03": "10", "04": "10", "05": "10",
              "06": "12", "07": "12", "08": "12", "09": "12", "10": "12",
              "11": "12", "12": "12"}
    for nn in range(1, 13):
        n = f"{nn:02d}"
        m = months[n]
        items.append((
            f"rookie-pp-{n}",
            f"{base}/2016/{m}/JrNBA17_Curriculum_Rookie_PP_{n}.pdf",
            f"Jr. NBA Rookie — Practice Plan {n}",
        ))
    return [
        {
            "url": url,
            "title": title,
            "content_type": "philosophy", "audience": ["coach"],
            "age_category": "U10,U12", "language": "en",
            "authority": "official", "level": "Rookie",
            "topic": "practice-plan", "region": "USA",
            "ruleset": "NBA", "chunk_type": "prose",
        }
        for _slug, url, title in items
    ]

JRNBA_SOURCES = _jrnba_starter() + _jrnba_rookie()

# Basketball England — primary URL is Cloudflare-blocked; mirror works for framework.
# Talent plan: try primary URL first; if 403 it'll fail and we report.
BE_SOURCES = [
    {
        "url": "https://www.basketballengland.co.uk/media/7137/talent-plan.pdf",
        "title": "Basketball England — Talent Plan",
        "content_type": "philosophy", "audience": ["coach"],
        "age_category": "U14,U16,U18", "language": "en",
        "authority": "official", "level": "n/a",
        "topic": "talent-development", "region": "EU",
        "ruleset": "FIBA", "chunk_type": "prose",
    },
    {
        "url": "https://www.sportstructures.com/media/0y2hddfb/player-development-framework.pdf",
        "title": "Basketball England — Player Development Framework Playbook",
        "content_type": "philosophy", "audience": ["coach"],
        "age_category": "all", "language": "en",
        "authority": "official", "level": "n/a",
        "topic": "talent-development", "region": "EU",
        "ruleset": "FIBA", "chunk_type": "prose",
    },
]

ALL_NEW = NL_BE_SOURCES + JRNBA_SOURCES + BE_SOURCES


# ---------- HTTP helpers ----------

def post_json(path: str, body: dict, timeout: int = 60) -> dict:
    req = urllib.request.Request(
        f"{API}{path}",
        data=json.dumps(body).encode("utf-8"),
        method="POST",
        headers={**HEADERS, "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def post_no_body(path: str, timeout: int = 60) -> dict:
    req = urllib.request.Request(
        f"{API}{path}", method="POST", headers=HEADERS,
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get_json(path: str, timeout: int = 30) -> dict:
    req = urllib.request.Request(f"{API}{path}", headers=HEADERS)
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ---------- job runner ----------

def poll(job_id: str, label: str) -> dict | None:
    """Poll until status != running. Print stage transitions only."""
    last_msg = ""
    deadline = time.time() + 90 * 60  # 90 min hard cap per job
    while time.time() < deadline:
        try:
            j = get_json(f"/admin/jobs/{job_id}")
        except Exception as e:
            print(f"  poll error: {e} — retrying")
            time.sleep(15)
            continue
        msg = f"{j.get('status'):8} {j.get('progress', 0):3}%  {j.get('stage', ''):12}  {j.get('message', '')}"
        if msg != last_msg:
            print(f"  {msg}")
            last_msg = msg
        if j.get("status") in ("done", "error"):
            return j
        time.sleep(20)
    print(f"  ⚠ poll timeout after 90 min for {label}")
    return None


def add_url(spec: dict) -> tuple[str, str | None]:
    """Returns (status, source_id_or_error)."""
    print(f"\n▶ ADD URL: {spec['title']}")
    print(f"  {spec['url'][:90]}")
    try:
        r = post_json("/admin/sources/url", spec)
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8", errors="replace")[:200]
        print(f"  ✗ HTTP {e.code}: {body}")
        return ("http_error", f"{e.code}: {body}")
    except Exception as e:
        print(f"  ✗ exception: {e}")
        return ("error", str(e))
    job_id = r.get("job_id")
    if not job_id:
        return ("no_job", str(r))
    final = poll(job_id, spec["title"])
    if final is None:
        return ("timeout", job_id)
    return (final.get("status", "unknown"), final.get("source_id") or final.get("error", ""))


def reingest(source_id: str) -> tuple[str, str]:
    print(f"\n▶ REINGEST: {source_id}")
    try:
        r = post_no_body(f"/admin/sources/{source_id}/reingest")
    except Exception as e:
        print(f"  ✗ {e}")
        return ("error", str(e))
    job_id = r.get("job_id", "")
    final = poll(job_id, source_id)
    if final is None:
        return ("timeout", job_id)
    return (final.get("status", "unknown"), final.get("chunk_count") or final.get("error", ""))


# ---------- main ----------

def main() -> None:
    print(f"API: {API}")
    print(f"Reingest: {len(REINGEST_IDS)} existing | New: {len(ALL_NEW)} sources")
    print(f"Total operations: {len(REINGEST_IDS) + len(ALL_NEW)}")
    print("=" * 60)

    results: list[tuple[str, str, str]] = []  # (kind, label, status)

    # Reingest existing first (page-aware chunker → updated locators)
    for sid in REINGEST_IDS:
        status, info = reingest(sid)
        results.append(("reingest", sid, f"{status}: {info}"))

    # New sources
    for spec in ALL_NEW:
        status, info = add_url(spec)
        results.append(("new", spec["title"], f"{status}: {info}"))

    # Summary
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    ok = sum(1 for _, _, s in results if s.startswith("done"))
    failed = [(k, label, s) for k, label, s in results if not s.startswith("done")]
    print(f"OK:     {ok}/{len(results)}")
    print(f"Failed: {len(failed)}")
    if failed:
        print("\nFailed details:")
        for kind, label, status in failed:
            print(f"  [{kind}] {label[:60]:60} → {status[:120]}")


if __name__ == "__main__":
    main()
