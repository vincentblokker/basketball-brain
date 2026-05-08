"""Admin endpoints for source management. Protected by ADMIN_TOKEN bearer."""
from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel

from app.admin.auth import require_admin
from app.admin.sources_manager import SourcesManager
from app.config import settings
from app.deps import get_bm25, get_store
from app.retrieval.bm25_index import BM25Index
from app.retrieval.chroma_store import ChromaStore

router = APIRouter(prefix="/admin", tags=["admin"])

_AdminDep = Depends(require_admin)
_StoreDep = Depends(get_store)


def _manager(store: ChromaStore) -> SourcesManager:
    return SourcesManager(Path(settings.raw_dir), store)


def _rebuild_bm25() -> None:
    """Drop the cached BM25 index so the next /query rebuilds it."""
    get_bm25.cache_clear()


class AddUrlRequest(BaseModel):
    url: str
    title: str
    content_type: str = "general"
    audience: list[str] | None = None
    age_category: str = "all"
    language: str = "nl"


@router.post("/auth/check", dependencies=[_AdminDep])
def check_token() -> dict[str, bool]:
    """Used by frontend to verify the stored admin token."""
    return {"ok": True}


@router.get("/sources", dependencies=[_AdminDep])
def list_sources(store: ChromaStore = _StoreDep) -> dict[str, Any]:
    return {"sources": _manager(store).list_sources()}


@router.post("/sources/url", dependencies=[_AdminDep])
def add_url(req: AddUrlRequest, store: ChromaStore = _StoreDep) -> dict[str, Any]:
    try:
        result = _manager(store).add_url(
            url=req.url,
            title=req.title,
            content_type=req.content_type,
            audience=req.audience,
            age_category=req.age_category,
            language=req.language,
        )
    except httpx.HTTPError as e:
        raise HTTPException(status_code=400, detail=f"Failed to fetch URL: {e}") from e
    _rebuild_bm25()
    return result


@router.post("/sources/upload", dependencies=[_AdminDep])
async def upload_file(
    file: UploadFile = File(...),
    title: str = Form(...),
    content_type: str = Form("general"),
    audience: str = Form("all"),  # comma-separated
    age_category: str = Form("all"),
    language: str = Form("nl"),
    source_url: str = Form(""),
    store: ChromaStore = _StoreDep,
) -> dict[str, Any]:
    body = await file.read()
    try:
        result = _manager(store).add_file(
            filename=file.filename or "upload.bin",
            body=body,
            title=title,
            content_type=content_type,
            audience=[a.strip() for a in audience.split(",") if a.strip()],
            age_category=age_category,
            language=language,
            source_url=source_url,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
    _rebuild_bm25()
    return result


@router.delete("/sources/{source_id}", dependencies=[_AdminDep])
def delete_source(source_id: str, store: ChromaStore = _StoreDep) -> dict[str, Any]:
    try:
        result = _manager(store).delete_source(source_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Source not found: {source_id}") from e
    _rebuild_bm25()
    return result


@router.post("/sources/{source_id}/reingest", dependencies=[_AdminDep])
def reingest_source(source_id: str, store: ChromaStore = _StoreDep) -> dict[str, Any]:
    try:
        result = _manager(store).reingest(source_id)
    except KeyError as e:
        raise HTTPException(status_code=404, detail=f"Source not found: {source_id}") from e
    _rebuild_bm25()
    return result


# Suppress unused-import warning — BM25Index is needed for type signatures elsewhere
_BM25_HINT = BM25Index
