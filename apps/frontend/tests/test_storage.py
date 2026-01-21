from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.storage import Storage


@pytest.mark.asyncio
async def test_store_trace_calls_db():
    storage = Storage()
    fake_trace = {"foo": "bar"}

    mock_execute = AsyncMock()
    mock_conn = MagicMock()
    mock_conn.execute = mock_execute
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
    fake_log = {"bar": "baz"}

    mock_execute = AsyncMock()
    mock_conn = MagicMock()
    mock_conn.execute = mock_execute
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
    fake_metric = {"baz": "qux"}

    mock_execute = AsyncMock()
    mock_conn = MagicMock()
    mock_conn.execute = mock_execute
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
