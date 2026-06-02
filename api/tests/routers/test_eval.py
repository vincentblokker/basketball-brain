from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.config import settings
from app.deps import get_bm25, get_generator, get_metrics, get_store
from app.main import app


@pytest.fixture
def client(monkeypatch):
    # Set a token so require_admin rejects with 401 (not the 503 "disabled").
    monkeypatch.setattr(settings, "admin_token", "secret-token")
    # Stub the heavy deps — the auth check fires before the handler, so these
    # are never exercised, but overriding keeps the test free of real I/O.
    app.dependency_overrides[get_store] = lambda: MagicMock()
    app.dependency_overrides[get_bm25] = lambda: MagicMock()
    app.dependency_overrides[get_generator] = lambda: MagicMock()
    app.dependency_overrides[get_metrics] = lambda: MagicMock()
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_eval_run_requires_admin_token(client):
    # No token -> rejected before any paid LLM call can run.
    assert client.get("/eval/run").status_code == 401


def test_eval_run_rejects_wrong_token(client):
    resp = client.get("/eval/run", headers={"Authorization": "Bearer wrong"})
    assert resp.status_code == 401
