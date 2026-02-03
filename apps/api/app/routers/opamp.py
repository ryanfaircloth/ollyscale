"""OpAMP (Open Agent Management Protocol) router for OTel Collector configuration management."""

import logging
from typing import Any

import httpx
from fastapi import APIRouter, HTTPException

from app.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/opamp", tags=["opamp"])

# OpAMP server endpoints (from environment or default to localhost)
OPAMP_BASE_URL = settings.OPAMP_SERVER_URL


@router.get("/status")
async def get_opamp_status() -> dict[str, Any]:
    """Get OpAMP server status and connected agents.

    Returns:
        dict with status, agent_count, and agents details

    Raises:
        HTTPException: If OpAMP server is unreachable
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OPAMP_BASE_URL}/status")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Failed to connect to OpAMP server: {e}")
        raise HTTPException(status_code=503, detail="OpAMP server unavailable") from e


@router.get("/config")
async def get_collector_config() -> dict[str, Any]:
    """Get current OTel Collector configuration.

    Returns:
        dict with config (YAML string) or status message

    Raises:
        HTTPException: If OpAMP server is unreachable or config retrieval fails
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OPAMP_BASE_URL}/config")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Failed to get collector config: {e}")
        raise HTTPException(status_code=503, detail="Failed to retrieve collector configuration") from e


@router.post("/config")
async def update_collector_config(payload: dict[str, Any]) -> dict[str, Any]:
    """Update OTel Collector configuration via OpAMP.

    Args:
        payload: dict with 'config' key containing YAML configuration

    Returns:
        dict with success status and message

    Raises:
        HTTPException: If validation fails or OpAMP server rejects config
    """
    if "config" not in payload:
        raise HTTPException(status_code=422, detail="Missing 'config' field in request body")

    config_yaml = payload["config"]
    if not isinstance(config_yaml, str):
        raise HTTPException(status_code=422, detail="'config' must be a string")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{OPAMP_BASE_URL}/config", json={"config": config_yaml})
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Failed to update collector config: {e}")
        # Try to extract error details from response
        error_detail = "Failed to update collector configuration"
        if hasattr(e, "response") and e.response is not None:
            try:
                error_data = e.response.json()
                error_detail = error_data.get("detail", error_detail)
            except Exception:
                pass
        raise HTTPException(status_code=503, detail=error_detail) from e


@router.get("/templates")
async def get_config_templates() -> dict[str, Any]:
    """Get available OTel Collector configuration templates.

    Returns:
        dict with 'templates' list containing template metadata

    Raises:
        HTTPException: If OpAMP server is unreachable
    """
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{OPAMP_BASE_URL}/templates")
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Failed to get templates: {e}")
        raise HTTPException(status_code=503, detail="Failed to retrieve templates") from e


@router.post("/validate")
async def validate_collector_config(payload: dict[str, Any]) -> dict[str, Any]:
    """Validate OTel Collector configuration without applying it.

    Args:
        payload: dict with 'config' key containing YAML configuration

    Returns:
        dict with 'valid' boolean and optional 'errors' list

    Raises:
        HTTPException: If OpAMP server is unreachable
    """
    if "config" not in payload:
        raise HTTPException(status_code=422, detail="Missing 'config' field in request body")

    config_yaml = payload["config"]
    if not isinstance(config_yaml, str):
        raise HTTPException(status_code=422, detail="'config' must be a string")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{OPAMP_BASE_URL}/validate", json={"config": config_yaml})
            response.raise_for_status()
            return response.json()
    except httpx.HTTPError as e:
        logger.error(f"Failed to validate config: {e}")
        raise HTTPException(status_code=503, detail="Failed to validate configuration") from e
