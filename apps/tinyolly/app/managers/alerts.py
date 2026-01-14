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

"""Alert manager for handling alert rules and notifications"""

import json
import logging
import os
import time

import aiohttp
from models import AlertRule

logger = logging.getLogger(__name__)


class AlertManager:
    """Manages alert rules and webhook notifications.

    Handles alerting for span errors and metric threshold breaches.
    """

    def __init__(self):
        """Initialize alert manager with empty rules."""
        self.rules: list[AlertRule] = []
        self._load_rules_from_env()

    def _load_rules_from_env(self):
        """Load alert rules from environment variables.

        Format: ALERT_RULES='[{"name":"...", "type":"...", "webhook_url":"...", ...}]'
        """
        rules_json = os.getenv("ALERT_RULES", "[]")
        try:
            rules_data = json.loads(rules_json)
            for rule_data in rules_data:
                self.rules.append(AlertRule(**rule_data))
            if self.rules:
                logger.info(f"Loaded {len(self.rules)} alert rules from environment")
        except Exception as e:
            logger.error(f"Error loading alert rules: {e}")

    def add_rule(self, rule: AlertRule):
        """Add a new alert rule.

        Args:
            rule (AlertRule): Alert rule to add
        """
        self.rules.append(rule)
        logger.info(f"Added alert rule: {rule.name}")

    def remove_rule(self, rule_name: str):
        """Remove an alert rule by name.

        Args:
            rule_name (str): Name of rule to remove
        """
        self.rules = [r for r in self.rules if r.name != rule_name]
        logger.info(f"Removed alert rule: {rule_name}")

    async def check_span_error(self, span: dict):
        """Check if span has error and trigger alerts.

        Args:
            span (dict): Span data to check
        """
        # Check if span has error status
        status = span.get("status", {})
        if status.get("code") == 2:  # ERROR status code in OTLP
            for rule in self.rules:
                if not rule.enabled or rule.type != "span_error":
                    continue

                # Apply service filter if specified
                if rule.service_filter and span.get("serviceName") != rule.service_filter:
                    continue

                # Trigger alert
                await self._send_webhook(
                    rule,
                    {
                        "alert_type": "span_error",
                        "rule_name": rule.name,
                        "span_id": span.get("spanId"),
                        "trace_id": span.get("traceId"),
                        "service": span.get("serviceName"),
                        "operation": span.get("name"),
                        "error_message": status.get("message", "Unknown error"),
                        "timestamp": span.get("startTimeUnixNano"),
                    },
                )

    async def check_metric_threshold(self, metric_name: str, value: float):
        """Check if metric exceeds threshold and trigger alerts.

        Args:
            metric_name (str): Name of the metric
            value (float): Current metric value
        """
        for rule in self.rules:
            if not rule.enabled or rule.type != "metric_threshold":
                continue

            if rule.metric_name != metric_name:
                continue

            # Check threshold
            triggered = False
            if (
                (rule.comparison == "gt" and value > rule.threshold)
                or (rule.comparison == "lt" and value < rule.threshold)
                or (rule.comparison == "eq" and value == rule.threshold)
            ):
                triggered = True

            if triggered:
                await self._send_webhook(
                    rule,
                    {
                        "alert_type": "metric_threshold",
                        "rule_name": rule.name,
                        "metric_name": metric_name,
                        "current_value": value,
                        "threshold": rule.threshold,
                        "comparison": rule.comparison,
                        "timestamp": int(time.time() * 1e9),
                    },
                )

    async def _send_webhook(self, rule: AlertRule, payload: dict):
        """Send webhook notification.

        Args:
            rule (AlertRule): Alert rule that triggered
            payload (dict): Alert payload to send
        """
        try:
            async with (
                aiohttp.ClientSession() as session,
                session.post(
                    rule.webhook_url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                    timeout=aiohttp.ClientTimeout(total=5),
                ) as response,
            ):
                if response.status >= 400:
                    logger.error(f"Webhook failed: {response.status} for rule {rule.name}")
                else:
                    logger.info(f"Alert sent for rule {rule.name}")
        except Exception as e:
            logger.error(f"Error sending webhook for rule {rule.name}: {e}")
