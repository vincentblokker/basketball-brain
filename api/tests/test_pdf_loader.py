import tempfile
from pathlib import Path

from app.ingest.pdf_loader import load_text


def test_load_html_strips_nav_and_extracts_text():
    html = """
    <html><body>
      <nav>SHOULD_NOT_APPEAR_NAV</nav>
      <script>SHOULD_NOT_APPEAR_SCRIPT</script>
      <main>
        <h1>Basketbal</h1>
        <p>Basketbal is een teamsport.</p>
      </main>
      <footer>SHOULD_NOT_APPEAR_FOOTER</footer>
    </body></html>
    """
    with tempfile.NamedTemporaryFile(suffix=".html", delete=False, mode="w", encoding="utf-8") as f:
        f.write(html)
        path = Path(f.name)
    try:
        text = load_text(path)
        assert "Basketbal" in text
        assert "teamsport" in text
        assert "SHOULD_NOT_APPEAR_NAV" not in text
        assert "SHOULD_NOT_APPEAR_SCRIPT" not in text
        assert "SHOULD_NOT_APPEAR_FOOTER" not in text
    finally:
        path.unlink()


def test_load_txt_returns_raw():
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False, mode="w", encoding="utf-8") as f:
        f.write("Hello world")
        path = Path(f.name)
    try:
        assert load_text(path) == "Hello world"
    finally:
        path.unlink()


def test_unsupported_suffix_raises():
    import pytest
    with tempfile.NamedTemporaryFile(suffix=".xyz", delete=False) as f:
        path = Path(f.name)
    try:
        with pytest.raises(ValueError, match="Unsupported"):
            load_text(path)
    finally:
        path.unlink()
