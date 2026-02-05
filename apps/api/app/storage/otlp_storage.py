"""
OTLP Storage Wrapper

Combines logs, traces, and metrics storage for the OTLP receiver.
Provides a unified interface for storing OTLP telemetry data.
"""

import logging
from typing import Any

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.storage.attribute_promotion_config import AttributePromotionConfig
from app.storage.logs_storage import LogsStorage
from app.storage.metrics_storage import MetricsStorage
from app.storage.traces_storage import TracesStorage

logger = logging.getLogger(__name__)


class OtlpStorage:
    """
    Unified OTLP storage backend for the receiver.

    Manages database connection and provides access to all storage components.
    """

    def __init__(self, connection_string: str, config_path: str = "/config/attribute-promotion.yaml"):
        """
        Initialize OTLP storage.

        Args:
            connection_string: PostgreSQL connection string
            config_path: Path to attribute promotion configuration
        """
        self.connection_string = connection_string
        self.engine = None
        self.session: Session | None = None

        # Load attribute promotion configuration
        self.config = AttributePromotionConfig(base_config_path=config_path)
        logger.info(f"Loaded attribute promotion config from {config_path}")

        # Storage components (initialized after connect())
        self.logs: LogsStorage | None = None
        self.traces: TracesStorage | None = None
        self.metrics: MetricsStorage | None = None

    def connect(self):
        """Establish database connection and initialize storage components."""
        if self.engine is None:
            self.engine = create_engine(
                self.connection_string,
                pool_size=10,
                max_overflow=20,
                pool_pre_ping=True,
                pool_recycle=3600,
            )
            logger.info(f"Created database engine: {self.connection_string.split('@')[1]}")

        # Create session
        if self.session is None:
            self.session = Session(self.engine)
            logger.info("Created database session")

            # Initialize storage components
            self.logs = LogsStorage(self.session)
            self.traces = TracesStorage(self.session)
            self.metrics = MetricsStorage(self.session)
            logger.info("Initialized logs, traces, and metrics storage")

    def close(self):
        """Close database connection."""
        if self.session:
            self.session.close()
            self.session = None
            logger.info("Closed database session")

        if self.engine:
            self.engine.dispose()
            self.engine = None
            logger.info("Disposed database engine")

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
            result = self.logs.store_logs(resource_log)
            total_count += result.get("log_count", 0)

        self.session.commit()
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
            result = self.traces.store_traces(resource_span)
            total_count += result.get("span_count", 0)

        self.session.commit()
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
            result = self.metrics.store_metrics(resource_metric)
            total_count += result.get("data_point_count", 0)

        self.session.commit()
        return total_count
