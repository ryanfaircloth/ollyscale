import os

import pytest
from httpx import ASGITransport, AsyncClient

from app.main_entry import get_app


@pytest.mark.asyncio
async def test_healthz():
    os.environ["OLLYSCALE_MODE"] = "frontend"
    app = get_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/healthz")
        assert resp.status_code == 200
        assert resp.json() == {"status": "ok"}


@pytest.mark.asyncio
async def test_health_db(monkeypatch):
    os.environ["OLLYSCALE_MODE"] = "frontend"
    # Patch env for test Postgres (assumes local test DB is available)
    monkeypatch.setenv("PG_HOST", "localhost")
    monkeypatch.setenv("PG_PORT", "5432")
    monkeypatch.setenv("PG_USER", "postgres")
    monkeypatch.setenv("PG_PASSWORD", "postgres")
    monkeypatch.setenv("PG_DB", "postgres")
    app = get_app()
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.get("/health/db")
        assert resp.status_code == 200
        data = resp.json()
        assert "status" in data
        assert data["status"] in ("ok", "error")
        if data["status"] == "ok":
            assert "db" in data and "host" in data
        else:
            assert "error" in data
