from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.storage import Storage


@pytest.mark.asyncio
async def test_store_trace_calls_db():
    storage = Storage()
    fake_trace = {
        "trace_id": "abc",
        "span_id": "def",
        "parent_span_id": "ghi",
        "service_name": "svc",
        "operation_name": "op",
        "resource_jsonb": {"foo": "bar"},
        "start_time_unix_nano": 1,
        "end_time_unix_nano": 2,
        "status_code": 0,
        "kind": 1,
        "tenant_id": "t",
        "connection_id": "c",
        "attributes": {},
        "events": [],
        "links": [],
    }

    mock_execute = AsyncMock()
    mock_fetchrow = AsyncMock(side_effect=[{"service_id": 1}, {"operation_id": 2}, {"resource_id": 3}])
    mock_conn = MagicMock()
    mock_conn.execute = mock_execute
    mock_conn.fetchrow = mock_fetchrow
    acquire_cm = MagicMock()
    acquire_cm.__aenter__ = AsyncMock(return_value=mock_conn)
    acquire_cm.__aexit__ = AsyncMock(return_value=None)
    pool_cm = MagicMock()
    pool_cm.__aenter__ = AsyncMock(return_value=pool_cm)
    pool_cm.__aexit__ = AsyncMock(return_value=None)
    pool_cm.acquire.return_value = acquire_cm
    with patch("asyncpg.create_pool", return_value=pool_cm) as mock_create_pool:
        await storage.store_trace(fake_trace)
        assert mock_create_pool.called
        mock_conn.execute.assert_awaited()
        args, _ = mock_conn.execute.call_args
        assert "INSERT INTO spans_fact" in args[0]
        assert "$1" in args[0] and "$2" in args[0] and "$13" in args[0]


@pytest.mark.asyncio
async def test_store_log_calls_db():
    storage = Storage()
    fake_log = {
        "trace_id": "abc",
        "span_id": "def",
        "service_name": "svc",
        "resource_jsonb": {"foo": "bar"},
        "time_unix_nano": 1,
        "severity_text": "INFO",
        "body": "msg",
        "tenant_id": "t",
        "connection_id": "c",
        "attributes": {},
    }

    mock_execute = AsyncMock()
    mock_fetchrow = AsyncMock(side_effect=[{"service_id": 1}, {"resource_id": 2}])
    mock_conn = MagicMock()
    mock_conn.execute = mock_execute
    mock_conn.fetchrow = mock_fetchrow
    acquire_cm = MagicMock()
    acquire_cm.__aenter__ = AsyncMock(return_value=mock_conn)
    acquire_cm.__aexit__ = AsyncMock(return_value=None)
    pool_cm = MagicMock()
    pool_cm.__aenter__ = AsyncMock(return_value=pool_cm)
    pool_cm.__aexit__ = AsyncMock(return_value=None)
    pool_cm.acquire.return_value = acquire_cm
    with patch("asyncpg.create_pool", return_value=pool_cm) as mock_create_pool:
        await storage.store_log(fake_log)
        assert mock_create_pool.called
        mock_conn.execute.assert_awaited()
        args, _ = mock_conn.execute.call_args
        assert "INSERT INTO logs_fact" in args[0]
        assert "$1" in args[0] and "$10" in args[0]


@pytest.mark.asyncio
async def test_store_metric_calls_db():
    storage = Storage()
    fake_metric = {
        "service_name": "svc",
        "resource_jsonb": {"foo": "bar"},
        "name": "cpu",
        "time_unix_nano": 1,
        "value": 42.0,
        "tenant_id": "t",
        "connection_id": "c",
        "attributes": {},
    }

    mock_execute = AsyncMock()
    mock_fetchrow = AsyncMock(side_effect=[{"service_id": 1}, {"resource_id": 2}])
    mock_conn = MagicMock()
    mock_conn.execute = mock_execute
    mock_conn.fetchrow = mock_fetchrow
    acquire_cm = MagicMock()
    acquire_cm.__aenter__ = AsyncMock(return_value=mock_conn)
    acquire_cm.__aexit__ = AsyncMock(return_value=None)
    pool_cm = MagicMock()
    pool_cm.__aenter__ = AsyncMock(return_value=pool_cm)
    pool_cm.__aexit__ = AsyncMock(return_value=None)
    pool_cm.acquire.return_value = acquire_cm
    with patch("asyncpg.create_pool", return_value=pool_cm) as mock_create_pool:
        await storage.store_metric(fake_metric)
        assert mock_create_pool.called
        mock_conn.execute.assert_awaited()
        args, _ = mock_conn.execute.call_args
        assert "INSERT INTO metrics_fact" in args[0]
        assert "$1" in args[0] and "$8" in args[0]
