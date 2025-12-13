"""Shared dependencies for dependency injection"""

from functools import lru_cache
from tinyolly_common import Storage

from .config import settings
from .managers.websocket import ConnectionManager
from .managers.alerts import AlertManager


@lru_cache()
def get_storage() -> Storage:
    """Get Redis storage instance (singleton)"""
    return Storage(host=settings.redis_host, port=settings.redis_port)


# Singleton instances
_connection_manager = None
_alert_manager = None


def get_connection_manager() -> ConnectionManager:
    """Get WebSocket connection manager (singleton)"""
    global _connection_manager
    if _connection_manager is None:
        _connection_manager = ConnectionManager()
    return _connection_manager


def get_alert_manager() -> AlertManager:
    """Get alert manager (singleton)"""
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager
