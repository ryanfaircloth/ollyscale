"""
Attribute Promotion Configuration

Implements two-tier attribute promotion system:
1. Base promoted attributes (config/attribute-promotion.yaml) - enforced, shipped with app
2. Admin overrides (/config/attribute-overrides.yaml) - optional ConfigMap, deployment-specific

Merge strategy:
- Promote: Union of base + overrides (additive)
- Drop: Set from overrides (if present), applied before promotion check
"""

import logging
from pathlib import Path

import yaml

logger = logging.getLogger(__name__)


class AttributePromotionConfig:
    """
    Manages attribute promotion rules for OTLP signals.

    Loads base configuration (always present) and optional admin overrides.
    Provides efficient lookup for promotion and drop decisions.
    """

    def __init__(
        self,
        base_config_path: str = "/config/attribute-promotion.yaml",
        override_config_path: str = "/config/attribute-overrides.yaml",
    ):
        """
        Initialize attribute promotion configuration.

        Args:
            base_config_path: Path to base promoted attributes (enforced)
            override_config_path: Path to admin overrides (optional ConfigMap)
        """
        self.base_config_path = Path(base_config_path)
        self.override_config_path = Path(override_config_path)

        # Load configurations
        self._base_config = self._load_yaml(self.base_config_path, required=True)
        self._override_config = self._load_yaml(self.override_config_path, required=False)

        # Build merged promotion sets (union of base + overrides)
        self._promoted_attrs = self._build_promoted_sets()

        # Build drop set (from overrides only, takes precedence)
        self._drop_attrs = self._build_drop_set()

        logger.info(
            f"Loaded attribute promotion config: "
            f"base={self.base_config_path}, "
            f"overrides={self.override_config_path.exists()}, "
            f"promoted_count={sum(len(v) for v in self._promoted_attrs.values())}, "
            f"drop_count={len(self._drop_attrs)}"
        )

    def _load_yaml(self, path: Path, required: bool = True) -> dict:
        """
        Load YAML configuration file.

        Args:
            path: Path to YAML file
            required: If True, raise error on missing file

        Returns:
            Parsed YAML dict, or empty dict if not required and missing

        Raises:
            FileNotFoundError: If required file is missing
            yaml.YAMLError: If YAML parsing fails
        """
        if not path.exists():
            if required:
                raise FileNotFoundError(f"Required configuration file not found: {path}")
            logger.info(f"Optional configuration file not found: {path}")
            return {}

        try:
            with path.open("r") as f:
                config = yaml.safe_load(f)
                logger.debug(f"Loaded configuration from {path}")
                return config or {}
        except yaml.YAMLError as e:
            logger.error(f"Failed to parse YAML from {path}: {e}")
            raise

    def _build_promoted_sets(self) -> dict[str, set[str]]:
        """
        Build merged promotion sets from base + overrides.

        Structure: {
            'resource.string': {'service.name', 'service.namespace', ...},
            'resource.int': {...},
            'logs.string': {'log.level', 'log.logger', ...},
            ...
        }

        Returns:
            Dict mapping signal.type to set of promoted attribute keys
        """
        promoted: dict[str, set[str]] = {}

        # Load base promoted attributes
        base_promote = self._base_config.get("promote", {})
        for signal in ["resource", "scope", "logs", "spans", "metrics"]:
            signal_attrs = base_promote.get(signal, {})
            for value_type in ["string", "int", "double", "bool", "bytes"]:
                key = f"{signal}.{value_type}"
                promoted[key] = set(signal_attrs.get(value_type, []))

        # Merge override additions (union)
        if self._override_config:
            override_promote = self._override_config.get("promote", {})
            for signal in ["resource", "scope", "logs", "spans", "metrics"]:
                signal_attrs = override_promote.get(signal, {})
                for value_type in ["string", "int", "double", "bool", "bytes"]:
                    key = f"{signal}.{value_type}"
                    additional = set(signal_attrs.get(value_type, []))
                    promoted[key].update(additional)

        return promoted

    def _build_drop_set(self) -> set[str]:
        """
        Build drop set from override configuration.

        Drop list takes precedence over promotion - attributes in drop list
        are never stored, even if they would be promoted.

        Returns:
            Set of attribute keys to drop (signal-agnostic)
        """
        if not self._override_config:
            return set()

        drop_config = self._override_config.get("drop", {})
        drop_attrs: set[str] = set()

        # Collect drops from all signals
        for signal in ["resource", "scope", "logs", "spans", "metrics"]:
            signal_drops = drop_config.get(signal, [])
            drop_attrs.update(signal_drops)

        return drop_attrs

    def should_drop(self, key: str) -> bool:
        """
        Check if attribute should be dropped (not stored at all).

        Args:
            key: Attribute key (e.g., 'password', 'auth_token')

        Returns:
            True if attribute should be dropped
        """
        return key in self._drop_attrs

    def is_promoted(self, signal: str, key: str, value_type: str) -> bool:
        """
        Check if attribute should be promoted to dedicated column.

        Args:
            signal: Signal type ('resource', 'scope', 'logs', 'spans', 'metrics')
            key: Attribute key (e.g., 'service.name', 'http.status_code')
            value_type: Value type ('string', 'int', 'double', 'bool', 'bytes')

        Returns:
            True if attribute should be promoted
        """
        # Drop takes precedence
        if self.should_drop(key):
            return False

        # Check promotion set
        config_key = f"{signal}.{value_type}"
        return key in self._promoted_attrs.get(config_key, set())

    def get_promoted_keys(self, signal: str, value_type: str) -> set[str]:
        """
        Get all promoted keys for a signal and value type.

        Args:
            signal: Signal type ('resource', 'scope', 'logs', 'spans', 'metrics')
            value_type: Value type ('string', 'int', 'double', 'bool', 'bytes')

        Returns:
            Set of promoted attribute keys
        """
        config_key = f"{signal}.{value_type}"
        return self._promoted_attrs.get(config_key, set()).copy()

    def get_all_promoted_keys(self) -> dict[str, set[str]]:
        """
        Get all promoted keys across all signals and types.

        Returns:
            Dict mapping signal.type to set of promoted keys
        """
        return {k: v.copy() for k, v in self._promoted_attrs.items()}

    def get_drop_keys(self) -> set[str]:
        """
        Get all drop keys.

        Returns:
            Set of attribute keys to drop
        """
        return self._drop_attrs.copy()


# Global singleton instance (lazy-loaded)
_config_instance: AttributePromotionConfig | None = None


def get_attribute_promotion_config() -> AttributePromotionConfig:
    """
    Get global AttributePromotionConfig instance (singleton).

    Returns:
        Shared AttributePromotionConfig instance
    """
    global _config_instance
    if _config_instance is None:
        _config_instance = AttributePromotionConfig()
    return _config_instance
