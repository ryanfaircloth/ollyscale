"""Storage layer abstraction for ollyScale v2."""

from abc import ABC, abstractmethod
from typing import Any

from app.models.api import (
    Filter,
    LogRecord,
    Metric,
    PaginationRequest,
    Service,
    ServiceMapEdge,
    ServiceMapNode,
    TimeRange,
)


class StorageBackend(ABC):
    """Abstract storage backend interface."""

    @abstractmethod
    async def connect(self) -> None:
        """Establish connection to storage backend."""
        pass

    @abstractmethod
    async def close(self) -> None:
        """Close connection to storage backend."""
        pass

    @abstractmethod
    async def health_check(self) -> dict[str, Any]:
        """Check storage backend health."""
        pass

    # ==================== Trace Storage ====================

    @abstractmethod
    async def store_traces(self, resource_spans: list[dict[str, Any]]) -> int:
        """
        Store traces from OTLP ResourceSpans.

        Args:
            resource_spans: OTLP ResourceSpans array

        Returns:
            Number of spans stored
        """
        pass

    @abstractmethod
    async def search_traces(
        self,
        time_range: TimeRange,
        filters: list[Filter] | None = None,
        pagination: PaginationRequest | None = None,
    ) -> tuple[list[dict[str, Any]], bool, str | None]:
        """
        Search traces with filters and pagination.

        Args:
            time_range: Time range for query
            filters: Optional list of filters
            pagination: Optional pagination parameters

        Returns:
            Tuple of (traces, has_more, next_cursor)
        """
        pass

    @abstractmethod
    async def get_trace_by_id(self, trace_id: str) -> dict[str, Any] | None:
        """
        Get trace by ID.

        Args:
            trace_id: Trace ID (hex string)

        Returns:
            Trace with spans or None if not found
        """
        pass

    @abstractmethod
    async def search_spans(
        self,
        time_range: TimeRange,
        filters: list[Filter] | None = None,
        pagination: PaginationRequest | None = None,
    ) -> tuple[list, bool, str | None]:
        """
        Search spans with filters and pagination.

        Args:
            time_range: Time range for query
            filters: Optional list of filters
            pagination: Optional pagination parameters

        Returns:
            Tuple of (spans, has_more, next_cursor)
        """
        pass

    # ==================== Log Storage ====================

    @abstractmethod
    async def store_logs(self, resource_logs: list[dict[str, Any]]) -> int:
        """
        Store logs from OTLP ResourceLogs.

        Args:
            resource_logs: OTLP ResourceLogs array

        Returns:
            Number of log records stored
        """
        pass

    @abstractmethod
    async def search_logs(
        self,
        time_range: TimeRange,
        filters: list[Filter] | None = None,
        pagination: PaginationRequest | None = None,
    ) -> tuple[list[LogRecord], bool, str | None]:
        """
        Search logs with filters and pagination.

        Args:
            time_range: Time range for query
            filters: Optional list of filters
            pagination: Optional pagination parameters

        Returns:
            Tuple of (logs, has_more, next_cursor)
        """
        pass

    # ==================== Metric Storage ====================

    @abstractmethod
    async def store_metrics(self, resource_metrics: list[dict[str, Any]]) -> int:
        """
        Store metrics from OTLP ResourceMetrics.

        Args:
            resource_metrics: OTLP ResourceMetrics array

        Returns:
            Number of metric data points stored
        """
        pass

    @abstractmethod
    async def search_metrics(
        self,
        time_range: TimeRange,
        metric_names: list[str] | None = None,
        filters: list[Filter] | None = None,
        pagination: PaginationRequest | None = None,
    ) -> tuple[list[Metric], bool, str | None]:
        """
        Search metrics with filters and pagination.

        Args:
            time_range: Time range for query
            metric_names: Optional list of metric names to filter
            filters: Optional list of filters
            pagination: Optional pagination parameters

        Returns:
            Tuple of (metrics, has_more, next_cursor)
        """
        pass

    @abstractmethod
    async def get_metric_detail(
        self,
        metric_name: str,
        time_range: TimeRange,
        filters: list[Filter] | None = None,
        include_attributes: bool = False,
    ) -> dict[str, Any] | None:
        """
        Get detailed time-series data for a specific metric.

        Args:
            metric_name: Name of metric to retrieve
            time_range: Time range for data
            filters: Optional filters for namespace, service, etc.
            include_attributes: If True, include unique attribute combinations for cardinality analysis

        Returns:
            Dict with metric metadata and series data, or None if not found.
            When include_attributes=True, response includes "attributes" key with list of unique label combinations.
        """
        pass

    # ==================== Service Catalog ====================

    @abstractmethod
    async def get_services(self, time_range: TimeRange | None = None) -> list[Service]:
        """
        Get service catalog with RED metrics.

        Args:
            time_range: Optional time range for RED metrics calculation

        Returns:
            List of services with metrics
        """
        pass

    @abstractmethod
    async def get_service_map(self, time_range: TimeRange) -> tuple[list[ServiceMapNode], list[ServiceMapEdge]]:
        """
        Get service dependency map.

        Args:
            time_range: Time range for map generation

        Returns:
            Tuple of (nodes, edges)
        """
        pass

    @abstractmethod
    async def get_namespaces(self) -> list[str]:
        """
        Get list of all namespaces for filtering.

        Returns:
            List of namespace strings (empty string for NULL namespace)
        """
        pass
