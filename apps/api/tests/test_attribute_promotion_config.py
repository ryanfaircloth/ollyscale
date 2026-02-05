"""
Unit tests for AttributePromotionConfig.

Tests base config loading, override merging, drop list precedence,
and efficient lookup operations.
"""

import tempfile
from pathlib import Path

import pytest
import yaml

import app.storage.attribute_promotion_config as config_module
from app.storage.attribute_promotion_config import (
    AttributePromotionConfig,
    get_attribute_promotion_config,
)


@pytest.fixture
def base_config_data():
    """Sample base configuration."""
    return {
        "promote": {
            "resource": {
                "string": ["service.name", "service.namespace", "cloud.provider"],
                "int": ["process.pid"],
            },
            "logs": {
                "string": ["log.level", "log.logger", "error.type"],
                "int": ["http.status_code"],
                "double": ["http.request.size"],
            },
            "spans": {
                "string": ["http.method", "http.route", "db.system"],
                "int": ["http.status_code", "gen_ai.usage.input_tokens"],
                "double": ["gen_ai.usage.cost"],
            },
            "metrics": {
                "string": ["endpoint", "method"],
                "int": ["status_code"],
            },
        }
    }


@pytest.fixture
def override_config_data():
    """Sample override configuration."""
    return {
        "promote": {
            "logs": {
                "string": ["custom.request_id"],
            },
            "spans": {
                "string": ["custom.transaction_id"],
                "int": ["custom.retry_count"],
            },
        },
        "drop": {
            "logs": ["password", "auth_token"],
            "spans": ["api_key", "secret"],
        },
    }


@pytest.fixture
def base_config_file(base_config_data):
    """Create temporary base config file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(base_config_data, f)
        path = Path(f.name)
    yield path
    path.unlink()


@pytest.fixture
def override_config_file(override_config_data):
    """Create temporary override config file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(override_config_data, f)
        path = Path(f.name)
    yield path
    path.unlink()


def test_load_base_config_only(base_config_file):
    """Test loading base configuration without overrides."""
    config = AttributePromotionConfig(
        base_config_path=str(base_config_file),
        override_config_path="/nonexistent/path.yaml",
    )

    # Verify resource promotion
    assert config.is_promoted("resource", "service.name", "string")
    assert config.is_promoted("resource", "service.namespace", "string")
    assert config.is_promoted("resource", "process.pid", "int")
    assert not config.is_promoted("resource", "unknown.attr", "string")

    # Verify logs promotion
    assert config.is_promoted("logs", "log.level", "string")
    assert config.is_promoted("logs", "http.status_code", "int")
    assert config.is_promoted("logs", "http.request.size", "double")

    # Verify no drops (no override file)
    assert not config.should_drop("password")


def test_merge_override_additive(base_config_file, override_config_file):
    """Test that overrides are additive (union with base)."""
    config = AttributePromotionConfig(
        base_config_path=str(base_config_file),
        override_config_path=str(override_config_file),
    )

    # Base attributes still promoted
    assert config.is_promoted("logs", "log.level", "string")
    assert config.is_promoted("logs", "http.status_code", "int")

    # Override additions also promoted
    assert config.is_promoted("logs", "custom.request_id", "string")
    assert config.is_promoted("spans", "custom.transaction_id", "string")
    assert config.is_promoted("spans", "custom.retry_count", "int")

    # Base span attributes still work
    assert config.is_promoted("spans", "http.method", "string")
    assert config.is_promoted("spans", "gen_ai.usage.input_tokens", "int")


def test_drop_list_precedence(base_config_file, override_config_file):
    """Test that drop list takes precedence over promotion."""
    config = AttributePromotionConfig(
        base_config_path=str(base_config_file),
        override_config_path=str(override_config_file),
    )

    # Verify drop list
    assert config.should_drop("password")
    assert config.should_drop("auth_token")
    assert config.should_drop("api_key")
    assert config.should_drop("secret")

    # Non-dropped attributes not affected
    assert not config.should_drop("log.level")
    assert not config.should_drop("http.method")

    # Dropped attributes are not promoted even if matched by promotion
    # (simulating a scenario where we add "password" to base promotion)
    config._promoted_attrs["logs.string"].add("password")
    assert not config.is_promoted("logs", "password", "string")  # Drop wins


def test_get_promoted_keys(base_config_file):
    """Test retrieving promoted keys for signal+type."""
    config = AttributePromotionConfig(
        base_config_path=str(base_config_file),
        override_config_path="/nonexistent/path.yaml",
    )

    # Get promoted string keys for logs
    logs_strings = config.get_promoted_keys("logs", "string")
    assert "log.level" in logs_strings
    assert "log.logger" in logs_strings
    assert "error.type" in logs_strings

    # Get promoted int keys for spans
    spans_ints = config.get_promoted_keys("spans", "int")
    assert "http.status_code" in spans_ints
    assert "gen_ai.usage.input_tokens" in spans_ints


def test_get_all_promoted_keys(base_config_file):
    """Test retrieving all promoted keys."""
    config = AttributePromotionConfig(
        base_config_path=str(base_config_file),
        override_config_path="/nonexistent/path.yaml",
    )

    all_keys = config.get_all_promoted_keys()

    # Verify structure
    assert "resource.string" in all_keys
    assert "logs.string" in all_keys
    assert "spans.int" in all_keys

    # Verify specific keys
    assert "service.name" in all_keys["resource.string"]
    assert "log.level" in all_keys["logs.string"]
    assert "http.status_code" in all_keys["spans.int"]


def test_get_drop_keys(base_config_file, override_config_file):
    """Test retrieving drop keys."""
    config = AttributePromotionConfig(
        base_config_path=str(base_config_file),
        override_config_path=str(override_config_file),
    )

    drop_keys = config.get_drop_keys()

    assert "password" in drop_keys
    assert "auth_token" in drop_keys
    assert "api_key" in drop_keys
    assert "secret" in drop_keys
    assert len(drop_keys) == 4


def test_missing_required_base_config():
    """Test error when required base config is missing."""
    with pytest.raises(FileNotFoundError, match="Required configuration"):
        AttributePromotionConfig(
            base_config_path="/nonexistent/base.yaml",
            override_config_path="/nonexistent/override.yaml",
        )


def test_invalid_yaml_raises_error(tmp_path):
    """Test error on invalid YAML syntax."""
    invalid_yaml = tmp_path / "invalid.yaml"
    invalid_yaml.write_text("{ invalid yaml content [")

    with pytest.raises(yaml.YAMLError):
        AttributePromotionConfig(
            base_config_path=str(invalid_yaml),
            override_config_path="/nonexistent/override.yaml",
        )


def test_empty_override_file(base_config_file, tmp_path):
    """Test handling of empty override file."""
    empty_override = tmp_path / "empty.yaml"
    empty_override.write_text("")

    config = AttributePromotionConfig(
        base_config_path=str(base_config_file),
        override_config_path=str(empty_override),
    )

    # Base config should still work
    assert config.is_promoted("logs", "log.level", "string")

    # No drops or additional promotions
    assert not config.should_drop("anything")


def test_singleton_instance(base_config_file):
    """Test global singleton pattern."""
    # Reset singleton
    config_module._config_instance = None

    # Create instance with test config
    instance1 = AttributePromotionConfig(
        base_config_path=str(base_config_file),
        override_config_path="/nonexistent/path.yaml",
    )

    # Set as singleton
    config_module._config_instance = instance1

    # Get instance - should return same one
    instance2 = get_attribute_promotion_config()

    # Should be same instance
    assert instance1 is instance2

    # Reset for other tests
    config_module._config_instance = None


def test_signal_types_coverage(base_config_file):
    """Test all signal types are handled."""
    config = AttributePromotionConfig(
        base_config_path=str(base_config_file),
        override_config_path="/nonexistent/path.yaml",
    )

    # Test all signals
    assert config.is_promoted("resource", "service.name", "string")
    assert config.is_promoted("logs", "log.level", "string")
    assert config.is_promoted("spans", "http.method", "string")
    assert config.is_promoted("metrics", "endpoint", "string")

    # Scope would be in real config (not in test fixture)
    # Just verify it doesn't crash
    assert not config.is_promoted("scope", "nonexistent", "string")


def test_value_type_coverage(base_config_file):
    """Test all value types are handled."""
    config = AttributePromotionConfig(
        base_config_path=str(base_config_file),
        override_config_path="/nonexistent/path.yaml",
    )

    # Test different value types
    assert config.is_promoted("resource", "service.name", "string")
    assert config.is_promoted("resource", "process.pid", "int")
    assert config.is_promoted("logs", "http.request.size", "double")

    # Bool and bytes not in test fixture but should not crash
    assert not config.is_promoted("logs", "nonexistent", "bool")
    assert not config.is_promoted("logs", "nonexistent", "bytes")
