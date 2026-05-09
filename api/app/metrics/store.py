"""SQLite-backed metrics store for the admin dashboard.

Two tables:
- queries: one row per /query call (timestamp, question, retrieval result, latency)
- eval_runs: one row per /eval/run call (config snapshot + summary metrics)

Aggregations live in this module so the router stays thin.
"""
from __future__ import annotations

import json
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any

_SCHEMA = """
CREATE TABLE IF NOT EXISTS queries (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    ts              REAL    NOT NULL,
    question        TEXT    NOT NULL,
    tenant_id       TEXT    NOT NULL,
    top_k           INTEGER NOT NULL,
    retrieved_count INTEGER NOT NULL,
    citation_source_ids TEXT NOT NULL,   -- JSON list of source_ids
    answer_length   INTEGER NOT NULL,
    is_oos          INTEGER NOT NULL,    -- 0/1
    mean_similarity REAL,                -- 0..1, NULL if not measurable
    latency_ms      REAL    NOT NULL,
    llm_model       TEXT    NOT NULL,
    error           TEXT
);
CREATE INDEX IF NOT EXISTS idx_queries_ts ON queries(ts);

CREATE TABLE IF NOT EXISTS eval_runs (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    ts                REAL    NOT NULL,
    config_json       TEXT    NOT NULL,
    n_questions       INTEGER NOT NULL,
    mean_recall       REAL    NOT NULL,
    mean_precision    REAL    NOT NULL,
    groundedness_rate REAL    NOT NULL,
    notes             TEXT
);
CREATE INDEX IF NOT EXISTS idx_eval_runs_ts ON eval_runs(ts);
"""


class MetricsStore:
    """Thread-safe SQLite store. One connection per call (cheap, simple)."""

    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        with self._connect() as conn:
            conn.executescript(_SCHEMA)
            conn.commit()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path, timeout=10.0)
        conn.row_factory = sqlite3.Row
        return conn

    # ---------- writers ----------

    def log_query(
        self,
        question: str,
        tenant_id: str,
        top_k: int,
        retrieved_count: int,
        citation_source_ids: list[str],
        answer_length: int,
        is_oos: bool,
        mean_similarity: float | None,
        latency_ms: float,
        llm_model: str,
        error: str | None = None,
    ) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """INSERT INTO queries
                   (ts, question, tenant_id, top_k, retrieved_count,
                    citation_source_ids, answer_length, is_oos, mean_similarity,
                    latency_ms, llm_model, error)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    time.time(), question, tenant_id, top_k, retrieved_count,
                    json.dumps(citation_source_ids), answer_length,
                    int(is_oos), mean_similarity, latency_ms, llm_model, error,
                ),
            )
            conn.commit()

    def log_eval_run(
        self,
        config: dict[str, Any],
        n_questions: int,
        mean_recall: float,
        mean_precision: float,
        groundedness_rate: float,
        notes: str | None = None,
    ) -> None:
        with self._lock, self._connect() as conn:
            conn.execute(
                """INSERT INTO eval_runs
                   (ts, config_json, n_questions, mean_recall, mean_precision,
                    groundedness_rate, notes)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (
                    time.time(), json.dumps(config), n_questions,
                    mean_recall, mean_precision, groundedness_rate, notes,
                ),
            )
            conn.commit()

    # ---------- readers ----------

    def overview(self) -> dict[str, Any]:
        """Top-level stats for the dashboard."""
        with self._connect() as conn:
            row = conn.execute(
                """SELECT COUNT(*)              AS total,
                          AVG(latency_ms)        AS mean_latency,
                          AVG(mean_similarity)   AS mean_sim,
                          AVG(CASE WHEN is_oos = 1 THEN 1.0 ELSE 0.0 END) AS oos_rate,
                          AVG(retrieved_count)   AS mean_retrieved
                   FROM queries"""
            ).fetchone()
            # latency percentiles via approximate quantile
            p50 = self._percentile(conn, "latency_ms", 0.5)
            p95 = self._percentile(conn, "latency_ms", 0.95)
            today = conn.execute(
                "SELECT COUNT(*) FROM queries WHERE ts >= ?",
                (time.time() - 86400,),
            ).fetchone()[0]
            week = conn.execute(
                "SELECT COUNT(*) FROM queries WHERE ts >= ?",
                (time.time() - 7 * 86400,),
            ).fetchone()[0]

        return {
            "total_queries": row["total"] or 0,
            "queries_last_24h": today or 0,
            "queries_last_7d": week or 0,
            "mean_latency_ms": row["mean_latency"] or 0,
            "p50_latency_ms": p50,
            "p95_latency_ms": p95,
            "mean_similarity": row["mean_sim"] or 0,
            "oos_rate": row["oos_rate"] or 0,
            "mean_retrieved": row["mean_retrieved"] or 0,
        }

    @staticmethod
    def _percentile(conn: sqlite3.Connection, column: str, pct: float) -> float:
        """Approximate percentile via ORDER BY + offset."""
        n = conn.execute("SELECT COUNT(*) FROM queries").fetchone()[0]
        if n == 0:
            return 0.0
        offset = max(0, int(n * pct) - 1)
        row = conn.execute(
            f"SELECT {column} FROM queries ORDER BY {column} LIMIT 1 OFFSET ?",
            (offset,),
        ).fetchone()
        return float(row[0]) if row else 0.0

    def top_sources(self, limit: int = 10) -> list[dict[str, Any]]:
        """Most-cited source_ids across all queries."""
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT citation_source_ids FROM queries"
            ).fetchall()
        counts: dict[str, int] = {}
        for r in rows:
            try:
                ids = json.loads(r["citation_source_ids"])
            except Exception:
                continue
            for sid in ids:
                counts[sid] = counts.get(sid, 0) + 1
        ranked = sorted(counts.items(), key=lambda kv: kv[1], reverse=True)[:limit]
        return [{"source_id": sid, "count": c} for sid, c in ranked]

    def recent_queries(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT ts, question, retrieved_count, citation_source_ids,
                          answer_length, is_oos, mean_similarity, latency_ms,
                          llm_model, error
                   FROM queries
                   ORDER BY ts DESC
                   LIMIT ?""",
                (limit,),
            ).fetchall()
        out: list[dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            try:
                d["citation_source_ids"] = json.loads(d["citation_source_ids"])
            except Exception:
                d["citation_source_ids"] = []
            d["is_oos"] = bool(d["is_oos"])
            out.append(d)
        return out

    def eval_history(self, limit: int = 50) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT ts, config_json, n_questions, mean_recall,
                          mean_precision, groundedness_rate, notes
                   FROM eval_runs
                   ORDER BY ts ASC
                   LIMIT ?""",
                (limit,),
            ).fetchall()
        out: list[dict[str, Any]] = []
        for r in rows:
            d = dict(r)
            try:
                d["config"] = json.loads(d.pop("config_json"))
            except Exception:
                d["config"] = {}
            out.append(d)
        return out

    def queries_per_day(self, days: int = 14) -> list[dict[str, Any]]:
        """Daily query counts for the last N days. Returns list ordered oldest-first."""
        with self._connect() as conn:
            rows = conn.execute(
                """SELECT date(ts, 'unixepoch') AS day, COUNT(*) AS n
                   FROM queries
                   WHERE ts >= ?
                   GROUP BY day
                   ORDER BY day""",
                (time.time() - days * 86400,),
            ).fetchall()
        return [{"day": r["day"], "count": r["n"]} for r in rows]
