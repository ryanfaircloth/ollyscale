"""
OTLP Storage Wrapper

Combines logs, traces, and metrics storage for the OTLP receiver.
Provides a unified interface for storing OTLP telemetry data.

CRITICAL: Uses two-engine pattern for deadlock-free multi-process ingestion:
- autocommit_engine: For dimension upserts (resource, scope, attribute keys)
- engine: For transactional fact inserts (logs, spans, metrics)
"""

import logging
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.engine import Engine

from app.storage.attribute_promotion_config import AttributePromotionConfig
from app.storage.logs_storage import LogsStorage
from app.storage.metrics_storage import MetricsStorage
from app.storage.traces_storage import TracesStorage

logger = logging.getLogger(__name__)


class OtlpStorage:
    """
    Unified OTLP storage backend for the receiver.

    Manages database connection and provides access to all storage components.
    Uses two-engine pattern (normal + autocommit) for multi-process safety.
    """

    def __init__(self, connection_string: str, config_path: str = "/config/attribute-promotion.yaml"):
        """
        Initialize OTLP storage.

        Args:
            connection_string: PostgreSQL connection string
            config_path: Path to attribute promotion configuration
        """
        self.connection_string = connection_string
        self.engine: Engine | None = None  # For fact inserts with explicit transactions
        self.autocommit_engine: Engine | None = None  # For dimension upserts with autocommit

        # Load attribute promotion configuration
        self.config = AttributePromotionConfig(base_config_path=config_path)
        logger.info(f"Loaded attribute promotion config from {config_path}")

        # Storage components (initialized after connect())
        self.logs: LogsStorage | None = None
        self.traces: TracesStorage | None = None
        self.metrics: MetricsStorage | None = None

    def connect(self):
        """Establish database engines and initialize storage components."""
        if self.engine is None:
            # Normal engine for fact inserts with explicit transactions
            self.engine = create_engine(
                self.connection_string,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
            logger.info(f"Created transactional engine: {self.connection_string.split('@')[1]}")

        if self.autocommit_engine is None:
            # Autocommit engine for dimension upserts (idempotent, multi-process safe)
            self.autocommit_engine = create_engine(
                self.connection_string,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
                execution_options={"isolation_level": "AUTOCOMMIT"},
            )
            logger.info(f"Created autocommit engine: {self.connection_string.split('@')[1]}")

        # Initialize storage components (they will use correct engines)
        self.logs = LogsStorage(self.engine, self.autocommit_engine, self.config)
        self.traces = TracesStorage(self.engine, self.autocommit_engine, self.config)
        self.metrics = MetricsStorage(self.engine, self.autocommit_engine, self.config)
        logger.info("Initialized logs, traces, and metrics storage")

    def close(self):
        """Close database connections."""
        if self.engine:
            self.engine.dispose()
            self.engine = None
            logger.info("Disposed transactional engine")

        if self.autocommit_engine:
            self.autocommit_engine.dispose()
            self.autocommit_engine = None
            logger.info("Disposed autocommit engine")

    def store_logs(self, resource_logs: list[dict[str, Any]]) -> int:
        """
        Store OTLP log records.

        Args:
            resource_logs: List of OTLP ResourceLogs

        Returns:
            Number of log records stored
        """
        if not self.logs:
            raise RuntimeError("Storage not connected - call connect() first")

        total_count = 0
        for resource_log in resource_logs:
            count = self.logs.store_logs(resource_log)
            total_count += count

        return total_count

    def store_traces(self, resource_spans: list[dict[str, Any]]) -> int:
        """
        Store OTLP span records.

        Args:
            resource_spans: List of OTLP ResourceSpans

        Returns:
            Number of spans stored
        """
        if not self.traces:
            raise RuntimeError("Storage not connected - call connect() first")

        total_count = 0
        for resource_span in resource_spans:
            count = self.traces.store_traces(resource_span)
            total_count += count

        return total_count

    def store_metrics(self, resource_metrics: list[dict[str, Any]]) -> int:
        """
        Store OTLP metric data points.

        Args:
            resource_metrics: List of OTLP ResourceMetrics

        Returns:
            Number of data points stored
        """
        if not self.metrics:
            raise RuntimeError("Storage not connected - call connect() first")

        total_count = 0
        for resource_metric in resource_metrics:
            count = self.metrics.store_metrics(resource_metric)
            total_count += count

        return total_count
