"""Per-page PNG screenshots of source PDFs for the citation viewer.

Produces ``/app/data/pages/{source_id}/page-{N:04d}.png`` for every page in
a PDF. HTML/text sources are skipped silently (no pages).
"""
from __future__ import annotations

import shutil
from pathlib import Path

from pdf2image import convert_from_path


def extract_pages(pdf_path: Path, out_dir: Path, dpi: int = 100) -> int:
    """Render every page of ``pdf_path`` as a PNG into ``out_dir``.

    Wipes the existing dir first to avoid stale images. Returns page count.
    Returns 0 if file isn't a PDF or rendering fails.
    """
    if pdf_path.suffix.lower() != ".pdf":
        return 0

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    try:
        pages = convert_from_path(str(pdf_path), dpi=dpi, fmt="png")
    except Exception as e:
        # Don't crash ingest just because page rendering failed.
        print(f"WARN: page rendering failed for {pdf_path.name}: {e}")
        return 0

    for i, img in enumerate(pages, start=1):
        target = out_dir / f"page-{i:04d}.png"
        img.save(target, "PNG", optimize=True)
    return len(pages)


def page_url(source_id: str, page: int) -> str:
    """The public URL pattern, served by FastAPI's StaticFiles mount.
    Caddy strips the /api prefix so the on-the-wire URL is /api/pages/...
    """
    return f"/pages/{source_id}/page-{page:04d}.png"


def remove_pages(out_dir: Path) -> None:
    if out_dir.exists():
        shutil.rmtree(out_dir)
