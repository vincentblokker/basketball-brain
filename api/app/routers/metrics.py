"""Read-only metrics endpoints powering the admin dashboard."""
from typing import Any

from fastapi import APIRouter, Depends, Query

from app.admin.auth import require_admin
from app.deps import get_metrics
from app.metrics.store import MetricsStore

router = APIRouter(prefix="/admin/metrics", tags=["admin", "metrics"])

_AdminDep = Depends(require_admin)
_MetricsDep = Depends(get_metrics)


@router.get("/overview", dependencies=[_AdminDep])
def overview(metrics: MetricsStore = _MetricsDep) -> dict[str, Any]:
    return metrics.overview()


@router.get("/top-sources", dependencies=[_AdminDep])
def top_sources(
    limit: int = Query(default=10, ge=1, le=100),
    metrics: MetricsStore = _MetricsDep,
) -> dict[str, Any]:
    return {"sources": metrics.top_sources(limit=limit)}


@router.get("/recent", dependencies=[_AdminDep])
def recent(
    limit: int = Query(default=50, ge=1, le=500),
    metrics: MetricsStore = _MetricsDep,
) -> dict[str, Any]:
    return {"queries": metrics.recent_queries(limit=limit)}


@router.get("/eval-history", dependencies=[_AdminDep])
def eval_history(
    limit: int = Query(default=50, ge=1, le=500),
    metrics: MetricsStore = _MetricsDep,
) -> dict[str, Any]:
    return {"runs": metrics.eval_history(limit=limit)}


@router.get("/queries-per-day", dependencies=[_AdminDep])
def queries_per_day(
    days: int = Query(default=14, ge=1, le=90),
    metrics: MetricsStore = _MetricsDep,
) -> dict[str, Any]:
    return {"days": metrics.queries_per_day(days=days)}
