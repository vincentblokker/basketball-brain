from pathlib import Path
from typing import TypedDict

import pypdf
from bs4 import BeautifulSoup


class PageEntry(TypedDict):
    page: int | None  # 1-indexed PDF page number; None for non-PDF (HTML/text)
    text: str


def load_text(path: Path) -> str:
    """Legacy single-blob loader. Kept for tests/non-PDF fallback."""
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        return _load_pdf(path)
    if suffix in {".html", ".htm"}:
        return _load_html(path)
    if suffix in {".txt", ".md"}:
        return path.read_text(encoding="utf-8")
    raise ValueError(f"Unsupported file type: {suffix}")


def load_pages(path: Path) -> list[PageEntry]:
    """Page-aware loader. Returns list of {page, text}.

    For PDFs: one entry per page, page-number 1-indexed.
    For HTML/text: single entry with page=None (no native pagination).
    """
    suffix = path.suffix.lower()
    if suffix == ".pdf":
        reader = pypdf.PdfReader(str(path))
        return [
            {"page": i + 1, "text": page.extract_text() or ""}
            for i, page in enumerate(reader.pages)
        ]
    if suffix in {".html", ".htm"}:
        return [{"page": None, "text": _load_html(path)}]
    if suffix in {".txt", ".md"}:
        return [{"page": None, "text": path.read_text(encoding="utf-8")}]
    raise ValueError(f"Unsupported file type: {suffix}")


def _load_pdf(path: Path) -> str:
    reader = pypdf.PdfReader(str(path))
    return "\n\n".join(page.extract_text() or "" for page in reader.pages)


def _load_html(path: Path) -> str:
    soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "aside"]):
        tag.decompose()
    return soup.get_text("\n", strip=True)
