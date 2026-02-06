"""
MetricsStorage - OTLP metrics ingestion (STUB - Not Yet Implemented).

TODO: Implement metrics storage with correct transaction patterns following logs/traces pattern.

CRITICAL: When implemented, dimension upserts use autocommit (no locks), fact inserts use transactions.

Flow:
1. Upsert resource (autocommit) → resource_id
2. Upsert scope (autocommit) → scope_id
3. Upsert metric dimension (autocommit) → metric_id
4. Insert metric data point facts + attributes (transaction)
"""

import logging
from typing import Any

from sqlalchemy.engine import Engine

from app.storage.attribute_manager import AttributeManager
from app.storage.attribute_promotion_config import AttributePromotionConfig
from app.storage.resource_manager import ResourceManager

logger = logging.getLogger(__name__)


class MetricsStorage:
    """Storage handler for OTLP metrics (STUB - returns 0 for now)."""

    def __init__(
        self,
        engine: Engine,
        autocommit_engine: Engine,
        config: AttributePromotionConfig,
    ):
        """
        Initialize metrics storage.

        Args:
            engine: Transactional engine for fact inserts
            autocommit_engine: Autocommit engine for dimension upserts
            config: Attribute promotion configuration
        """
        self.engine = engine
        self.autocommit_engine = autocommit_engine
        self.config = config

        # Managers use autocommit engine for dimensions
        self.resource_mgr = ResourceManager(autocommit_engine, config)
        self.attr_mgr = AttributeManager(autocommit_engine, config)

        logger.warning("MetricsStorage initialized but NOT IMPLEMENTED - metrics will be logged and discarded")

    def store_metrics(self, resource_metrics: dict[str, Any]) -> int:
        """
        Store OTLP ResourceMetrics.

        STUB: Currently logs metrics but doesn't store them.

        Args:
            resource_metrics: Single OTLP ResourceMetrics dict

        Returns:
            0 (metrics not yet stored)
        """
        # Count data points for logging
        data_point_count = 0
        for scope_metrics in resource_metrics.get("scopeMetrics", []):
            for metric in scope_metrics.get("metrics", []):
                # Count data points across all metric types
                if "gauge" in metric:
                    data_point_count += len(metric["gauge"].get("dataPoints", []))
                elif "sum" in metric:
                    data_point_count += len(metric["sum"].get("dataPoints", []))
                elif "histogram" in metric:
                    data_point_count += len(metric["histogram"].get("dataPoints", []))
                elif "exponentialHistogram" in metric:
                    data_point_count += len(metric["exponentialHistogram"].get("dataPoints", []))
                elif "summary" in metric:
                    data_point_count += len(metric["summary"].get("dataPoints", []))

        if data_point_count > 0:
            logger.warning(
                f"STUB: Received {data_point_count} metric data points but metrics storage not implemented - discarding"
            )

        # Return 0 since we're not actually storing
        return 0
