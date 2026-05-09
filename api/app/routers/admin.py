"""Admin endpoints for source management. Protected by ADMIN_TOKEN bearer."""
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.admin.auth import require_admin
from app.admin.jobs import JobsManager
from app.admin.sources_manager import SourcesManager
from app.config import settings
from app.deps import get_bm25, get_jobs, get_store
from app.retrieval.chroma_store import ChromaStore

router = APIRouter(prefix="/admin", tags=["admin"])

_AdminDep = Depends(require_admin)
_StoreDep = Depends(get_store)
_JobsDep = Depends(get_jobs)


def _manager(store: ChromaStore) -> SourcesManager:
    return SourcesManager(Path(settings.raw_dir), store)


def _rebuild_bm25() -> None:
    """Drop the cached BM25 index so the next /query rebuilds it."""
    get_bm25.cache_clear()


def _make_callback(jobs: JobsManager, job_id: str):
    def cb(stage: str, pct: int, message: str) -> None:
        jobs.update(job_id, stage=stage, progress=pct, message=message)
    return cb


class AddUrlRequest(BaseModel):
    url: str
    title: str
    content_type: str = "general"
    audience: list[str] | None = None
    age_category: str = "all"
    language: str = "nl"
    # v2 schema fields — all optional, defaults preserve old behaviour
    authority: str = "supplementary"
    level: str = "n/a"
    topic: str | None = None
    region: str = "international"
    ruleset: str | None = None
    chunk_type: str = "prose"


@router.post("/auth/check", dependencies=[_AdminDep])
def check_token() -> dict[str, bool]:
    """Used by frontend to verify the stored admin token."""
    return {"ok": True}


@router.get("/sources", dependencies=[_AdminDep])
def list_sources(store: ChromaStore = _StoreDep) -> dict[str, Any]:
    return {"sources": _manager(store).list_sources()}


@router.get("/jobs/{job_id}", dependencies=[_AdminDep])
def get_job(job_id: str, jobs: JobsManager = _JobsDep) -> dict[str, Any]:
    job = jobs.get(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail="Job not found")
    return job.to_dict()


@router.get("/jobs", dependencies=[_AdminDep])
def list_jobs(jobs: JobsManager = _JobsDep) -> dict[str, Any]:
    return {"jobs": [j.to_dict() for j in jobs.list_recent()]}


# ---- ingest endpoints (return job_id immediately, work in background) ----


def _run_url_job(
    job_id: str,
    req: AddUrlRequest,
    store: ChromaStore,
    jobs: JobsManager,
) -> None:
    cb = _make_callback(jobs, job_id)
    try:
        result = _manager(store).add_url(
            url=req.url,
            title=req.title,
            content_type=req.content_type,
            audience=req.audience,
            age_category=req.age_category,
            language=req.language,
            authority=req.authority,
            level=req.level,
            topic=req.topic,
            region=req.region,
            ruleset=req.ruleset,
            chunk_type=req.chunk_type,
            on_stage=cb,
        )
        jobs.update(
            job_id,
            status="done",
            stage="done",
            progress=100,
            message=f"{result['chunk_count']} chunks geïndexeerd",
            source_id=result["id"],
            chunk_count=result["chunk_count"],
        )
        _rebuild_bm25()
    except Exception as e:
        jobs.update(
            job_id, status="error", stage="error", progress=0,
            message=str(e), error=str(e),
        )


def _run_upload_job(
    job_id: str,
    *,
    filename: str,
    body: bytes,
    title: str,
    content_type: str,
    audience: list[str],
    age_category: str,
    language: str,
    source_url: str,
    authority: str,
    level: str,
    topic: str | None,
    region: str,
    ruleset: str | None,
    chunk_type: str,
    store: ChromaStore,
    jobs: JobsManager,
) -> None:
    cb = _make_callback(jobs, job_id)
    try:
        result = _manager(store).add_file(
            filename=filename,
            body=body,
            title=title,
            content_type=content_type,
            audience=audience,
            age_category=age_category,
            language=language,
            source_url=source_url,
            authority=authority,
            level=level,
            topic=topic,
            region=region,
            ruleset=ruleset,
            chunk_type=chunk_type,
            on_stage=cb,
        )
        jobs.update(
            job_id,
            status="done",
            stage="done",
            progress=100,
            message=f"{result['chunk_count']} chunks geïndexeerd",
            source_id=result["id"],
            chunk_count=result["chunk_count"],
        )
        _rebuild_bm25()
    except Exception as e:
        jobs.update(
            job_id, status="error", stage="error", progress=0,
            message=str(e), error=str(e),
        )


def _run_reingest_job(
    job_id: str,
    source_id: str,
    store: ChromaStore,
    jobs: JobsManager,
) -> None:
    cb = _make_callback(jobs, job_id)
    try:
        result = _manager(store).reingest(source_id, on_stage=cb)
        jobs.update(
            job_id,
            status="done",
            stage="done",
            progress=100,
            message=f"{result['chunk_count']} chunks geïndexeerd",
            source_id=result["id"],
            chunk_count=result["chunk_count"],
        )
        _rebuild_bm25()
    except Exception as e:
        jobs.update(
            job_id, status="error", stage="error", progress=0,
            message=str(e), error=str(e),
        )


@router.post("/sources/url", dependencies=[_AdminDep], status_code=202)
def add_url(
    req: AddUrlRequest,
    background_tasks: BackgroundTasks,
    store: ChromaStore = _StoreDep,
    jobs: JobsManager = _JobsDep,
) -> dict[str, str]:
    job = jobs.create(kind="url")
    background_tasks.add_task(_run_url_job, job.id, req, store, jobs)
    return {"job_id": job.id}


@router.post("/sources/upload", dependencies=[_AdminDep], status_code=202)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    title: str = Form(...),
    content_type: str = Form("general"),
    audience: str = Form("all"),  # comma-separated
    age_category: str = Form("all"),
    language: str = Form("nl"),
    source_url: str = Form(""),
    authority: str = Form("supplementary"),
    level: str = Form("n/a"),
    topic: str = Form(""),
    region: str = Form("international"),
    ruleset: str = Form(""),
    chunk_type: str = Form("prose"),
    store: ChromaStore = _StoreDep,
    jobs: JobsManager = _JobsDep,
) -> dict[str, str]:
    body = await file.read()
    job = jobs.create(kind="upload")
    background_tasks.add_task(
        _run_upload_job,
        job.id,
        filename=file.filename or "upload.bin",
        body=body,
        title=title,
        content_type=content_type,
        audience=[a.strip() for a in audience.split(",") if a.strip()],
        age_category=age_category,
        language=language,
        source_url=source_url,
        authority=authority,
        level=level,
        topic=topic or None,
        region=region,
        ruleset=ruleset or None,
        chunk_type=chunk_type,
        store=store,
        jobs=jobs,
    )
    return {"job_id": job.id}


class UpdateSourceRequest(BaseModel):
    """Partial update — every field optional. Only known fields applied."""
    title: str | None = None
    content_type: str | None = None
    audience: list[str] | None = None
    age_category: str | None = None
    language: str | None = None
    url: str | None = None
    authority: str | None = None
    level: str | None = None
    topic: str | None = None
    region: str | None = None
    ruleset: str | None = None


@router.patch("/sources/{source_id}", dependencies=[_AdminDep])
def update_source(
    source_id: str,
    req: UpdateSourceRequest,
    store: ChromaStore = _StoreDep,
) -> dict[str, Any]:
    # Drop fields the caller didn't set so we don't clobber with None.
    updates = {k: v for k, v in req.model_dump().items() if v is not None}
    try:
        result = _manager(store).update_source(source_id, updates)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Source not found: {source_id}") from e
    _rebuild_bm25()
    return result


@router.post("/sources/{source_id}/regenerate-pages", dependencies=[_AdminDep])
def regenerate_pages(source_id: str, store: ChromaStore = _StoreDep) -> dict[str, Any]:
    """Re-render PDF page-thumbnails without re-embedding. Cheap."""
    try:
        return _manager(store).regenerate_pages(source_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Source not found: {source_id}") from e
    except FileNotFoundError as e:
        raise HTTPException(status_code=400, detail=f"Source file missing: {e}") from e


@router.delete("/sources/{source_id}", dependencies=[_AdminDep])
def delete_source(source_id: str, store: ChromaStore = _StoreDep) -> dict[str, Any]:
    try:
        result = _manager(store).delete_source(source_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Source not found: {source_id}") from e
    _rebuild_bm25()
    return result


@router.post("/sources/{source_id}/reingest", dependencies=[_AdminDep], status_code=202)
def reingest_source(
    source_id: str,
    background_tasks: BackgroundTasks,
    store: ChromaStore = _StoreDep,
    jobs: JobsManager = _JobsDep,
) -> dict[str, str]:
    # Verify the source exists upfront so we can 404 synchronously
    try:
        _manager(store)._read_manifest()  # noqa: SLF001 — internal check
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Manifest read error: {e}") from e
    job = jobs.create(kind="reingest")
    background_tasks.add_task(_run_reingest_job, job.id, source_id, store, jobs)
    return {"job_id": job.id}
