
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app


def valid_trace_payload():
    return {
        "resource_spans": [
            {
                "resource": {"attributes": [{"key": "service.name", "value": "test-service"}]},
                "spans": [
                    {
                        "trace_id": "abc123",
                        "span_id": "def456",
                        "name": "test-span",
                        "kind": 1,
                        "start_time_unix_nano": 1234567890,
                        "end_time_unix_nano": 1234567999,
                    }
                ],
            }
        ]
    }


def invalid_payload():
    return {"foo": "bar"}



@pytest.mark.asyncio
async def test_otlp_trace_valid():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/otlp", json=valid_trace_payload())
    assert resp.status_code == 200
    assert resp.json()["type"] == "trace"



@pytest.mark.asyncio
async def test_otlp_invalid():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        resp = await ac.post("/otlp", json=invalid_payload())
    assert resp.status_code == 400
    assert "error" in resp.json()
