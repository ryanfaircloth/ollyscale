# BSD 3-Clause License
#
# Copyright (c) 2025, Infrastructure Architects, LLC
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# 3. Neither the name of the copyright holder nor the names of its
#    contributors may be used to endorse or promote products derived from this
#    software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
# FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
# DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
# OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

"""Admin endpoints"""

import datetime
import time

import psutil
from fastapi import APIRouter, Depends
from models import AdminStatsResponse, AlertConfig, AlertRule

from common import Storage

from ..dependencies import get_alert_manager, get_storage
from ..managers.alerts import AlertManager

router = APIRouter(prefix="/admin", tags=["System"])


@router.get(
    "/stats",
    response_model=AdminStatsResponse,
    operation_id="admin_stats",
    summary="Get detailed system statistics",
    description="""
    Get comprehensive OllyScale performance and health metrics:

    - **Telemetry counts**: Traces, spans, logs, metrics
    - **Redis memory usage**: Current, peak, RSS
    - **Metric cardinality**: Current vs max, dropped count
    - **Connection stats**: Total connections, commands processed

    Useful for monitoring OllyScale's resource usage and performance.
    """,
)
async def admin_stats(storage: Storage = Depends(get_storage)):
    """Get detailed admin statistics including Redis memory and performance metrics"""
    stats = await storage.get_admin_stats()

    # Add uptime calculation
    process = psutil.Process()
    uptime_seconds = time.time() - process.create_time()
    uptime_str = str(datetime.timedelta(seconds=int(uptime_seconds)))
    stats["uptime"] = uptime_str

    return stats


@router.get("/alerts", response_model=AlertConfig, operation_id="get_alerts", summary="Get alert configuration")
async def get_alerts(alert_manager: AlertManager = Depends(get_alert_manager)):
    """Get all configured alert rules."""
    return AlertConfig(rules=alert_manager.rules)


@router.post("/alerts", response_model=AlertRule, operation_id="create_alert", summary="Create alert rule")
async def create_alert(rule: AlertRule, alert_manager: AlertManager = Depends(get_alert_manager)):
    """Create a new alert rule.

    **Span Error Alert Example:**
    ```json
    {
        "name": "API Errors",
        "type": "span_error",
        "enabled": true,
        "webhook_url": "https://hooks.slack.com/...",
        "service_filter": "api-service"
    }
    ```

    **Metric Threshold Alert Example:**
    ```json
    {
        "name": "High CPU",
        "type": "metric_threshold",
        "enabled": true,
        "webhook_url": "https://hooks.slack.com/...",
        "metric_name": "system.cpu.usage",
        "threshold": 80.0,
        "comparison": "gt"
    }
    ```
    """
    alert_manager.add_rule(rule)
    return rule


@router.delete("/alerts/{rule_name}", operation_id="delete_alert", summary="Delete alert rule")
async def delete_alert(rule_name: str, alert_manager: AlertManager = Depends(get_alert_manager)):
    """Delete an alert rule by name."""
    alert_manager.remove_rule(rule_name)
    return {"status": "ok", "message": f"Alert rule '{rule_name}' deleted"}
