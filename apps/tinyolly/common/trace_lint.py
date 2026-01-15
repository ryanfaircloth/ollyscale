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

"""
Trace Lint Module - Analyzes trace structures to identify unique flows and provide feedback.

This module computes trace flow signatures by hashing structural elements while ignoring
identifiers like IPs and user agents. It provides lint findings such as:
- Spans that should use auto-instrumentation
- Semantic convention violations
- Field naming issues
"""

import hashlib
import json
import re
from typing import Any

from .otlp_utils import get_attr_value, parse_attributes

# Semantic convention attributes (OpenTelemetry standard)
# https://opentelemetry.io/docs/specs/semconv/
SEMCONV_ATTRIBUTES = {
    "http.method",
    "http.request.method",
    "http.status_code",
    "http.response.status_code",
    "http.route",
    "http.target",
    "http.url",
    "http.scheme",
    "http.host",
    "http.server_name",
    "url.path",
    "url.full",
    "url.scheme",
    "net.host.name",
    "net.host.port",
    "net.peer.name",
    "net.peer.port",
    "db.system",
    "db.name",
    "db.statement",
    "db.operation",
    "messaging.system",
    "messaging.destination",
    "messaging.operation",
    "rpc.system",
    "rpc.service",
    "rpc.method",
    "error.type",
    "exception.type",
    "exception.message",
}

# Attributes that are identifiers (should be ignored for flow hashing)
IDENTIFIER_ATTRIBUTES = {
    "net.peer.ip",
    "net.host.ip",
    "client.address",
    "server.address",
    "http.client_ip",
    "user_agent.original",
    "http.user_agent",
    "enduser.id",
    "session.id",
    "trace.id",
    "span.id",
}

# Attributes that affect control flow (should be included in hash)
LOGIC_ATTRIBUTES = {
    "http.status_code",
    "http.response.status_code",
    "error.type",
    "exception.type",
    "exception.message",
    "db.operation",
    "messaging.operation",
    "rpc.method",
}


def _normalize_attribute_name(key: str) -> str:
    """Normalize attribute names to detect non-standard conventions."""
    return key.lower().replace("_", ".").replace("-", ".")


def _is_identifier_value(key: str, value: Any) -> bool:
    """Check if an attribute value is an identifier (IP, UUID, etc)."""
    if key in IDENTIFIER_ATTRIBUTES:
        return True

    if not isinstance(value, str):
        return False

    # IP address pattern
    if re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", value):
        return True

    # UUID pattern
    if re.match(r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$", value.lower()):
        return True

    return False


def _extract_span_structure(span: dict[str, Any]) -> dict[str, Any]:
    """Extract structural elements from a span for flow hashing.

    Args:
        span: Span data dictionary

    Returns:
        Dictionary containing structural elements (excludes identifiers)
    """
    # Parse attributes if in list format
    attrs = span.get("attributes", {})
    if isinstance(attrs, list):
        attrs = parse_attributes(attrs)

    structure = {
        "name": span.get("name", ""),
        "kind": span.get("kind", 0),
        "serviceName": span.get("serviceName", "unknown"),
    }

    # Include logic-affecting attributes
    logic_attrs = {}
    for key, value in attrs.items():
        if not _is_identifier_value(key, value):
            # Include logic attributes and semantic conventions
            normalized_key = _normalize_attribute_name(key)
            if any(normalized_key.startswith(prefix) for prefix in ["http.", "db.", "rpc.", "messaging.", "error.", "exception."]):
                logic_attrs[key] = value

    if logic_attrs:
        structure["attributes"] = logic_attrs

    # Include status information
    status = span.get("status", {})
    if status:
        structure["status"] = {"code": status.get("code", 0)}

    return structure


def compute_trace_flow_hash(spans: list[dict[str, Any]]) -> str:
    """Compute a hash representing the trace flow structure.

    Args:
        spans: List of span dictionaries

    Returns:
        Hash string representing the trace flow
    """
    # Sort spans by start time to get consistent ordering
    sorted_spans = sorted(spans, key=lambda s: s.get("startTimeUnixNano", s.get("start_time", 0)))

    # Extract structures
    structures = [_extract_span_structure(span) for span in sorted_spans]

    # Create deterministic JSON representation
    flow_json = json.dumps(structures, sort_keys=True)

    # Compute hash
    return hashlib.sha256(flow_json.encode()).hexdigest()[:16]


def _check_attribute_naming(span: dict[str, Any]) -> list[dict[str, Any]]:
    """Check for attribute naming issues.

    Args:
        span: Span data dictionary

    Returns:
        List of lint findings
    """
    findings = []
    attrs = span.get("attributes", {})
    if isinstance(attrs, list):
        attrs = parse_attributes(attrs)

    for key in attrs.keys():
        normalized = _normalize_attribute_name(key)

        # Check for underscore instead of dot
        if "_" in key and "." not in key:
            # Check if there's a semantic convention equivalent
            for semconv in SEMCONV_ATTRIBUTES:
                if semconv.replace(".", "_") == key or semconv.replace(".", "_").lower() == key.lower():
                    findings.append(
                        {
                            "severity": "warning",
                            "type": "naming",
                            "message": f"Attribute '{key}' should use semantic convention '{semconv}'",
                            "suggestion": f"Rename '{key}' to '{semconv}'",
                            "span_name": span.get("name", "unknown"),
                        }
                    )
                    break

    # Check for missing standard HTTP attributes on HTTP spans
    span_name = span.get("name", "").lower()
    if any(method in span_name for method in ["get", "post", "put", "delete", "patch", "head", "options"]):
        if "http.method" not in attrs and "http.request.method" not in attrs:
            findings.append(
                {
                    "severity": "info",
                    "type": "missing_attribute",
                    "message": f"HTTP span '{span.get('name')}' missing http.method attribute",
                    "suggestion": "Add http.method or http.request.method attribute for HTTP spans",
                    "span_name": span.get("name", "unknown"),
                }
            )

    return findings


def _check_auto_instrumentation(span: dict[str, Any]) -> list[dict[str, Any]]:
    """Check if span should be handled by auto-instrumentation.

    Args:
        span: Span data dictionary

    Returns:
        List of lint findings
    """
    findings = []
    span_name = span.get("name", "")
    attrs = span.get("attributes", {})
    if isinstance(attrs, list):
        attrs = parse_attributes(attrs)

    # Check for HTTP client/server spans
    http_method = get_attr_value(span, ["http.method", "http.request.method"])
    if http_method:
        kind = span.get("kind", 0)
        # Server spans (kind=2) and client spans (kind=3)
        if kind in [2, 3]:
            # Check if this looks like a manually instrumented span
            if not any(key.startswith("http.") for key in attrs.keys()):
                findings.append(
                    {
                        "severity": "info",
                        "type": "auto_instrumentation",
                        "message": f"HTTP span '{span_name}' may benefit from auto-instrumentation",
                        "suggestion": "Consider using OpenTelemetry auto-instrumentation for HTTP requests",
                        "span_name": span_name,
                    }
                )

    # Check for database spans
    db_system = get_attr_value(span, ["db.system"])
    if db_system or any(db in span_name.lower() for db in ["sql", "select", "insert", "update", "delete", "query", "database", "mongo", "redis", "postgres", "mysql"]):
        if not db_system:
            findings.append(
                {
                    "severity": "warning",
                    "type": "missing_attribute",
                    "message": f"Database span '{span_name}' missing db.system attribute",
                    "suggestion": "Add db.system attribute for database operations",
                    "span_name": span_name,
                }
            )

    return findings


def lint_trace(spans: list[dict[str, Any]]) -> dict[str, Any]:
    """Lint a trace and return findings.

    Args:
        spans: List of span dictionaries

    Returns:
        Dictionary containing flow hash and lint findings
    """
    flow_hash = compute_trace_flow_hash(spans)
    findings = []

    for span in spans:
        # Check attribute naming
        findings.extend(_check_attribute_naming(span))

        # Check auto-instrumentation opportunities
        findings.extend(_check_auto_instrumentation(span))

    # Deduplicate findings by message
    unique_findings = []
    seen_messages = set()
    for finding in findings:
        msg = finding["message"]
        if msg not in seen_messages:
            seen_messages.add(msg)
            unique_findings.append(finding)

    return {
        "flow_hash": flow_hash,
        "findings": unique_findings,
        "span_count": len(spans),
        "severity_counts": {
            "error": len([f for f in unique_findings if f["severity"] == "error"]),
            "warning": len([f for f in unique_findings if f["severity"] == "warning"]),
            "info": len([f for f in unique_findings if f["severity"] == "info"]),
        },
    }


def compute_flow_summary(spans: list[dict[str, Any]]) -> dict[str, Any]:
    """Compute a summary of the trace flow for display.

    Args:
        spans: List of span dictionaries

    Returns:
        Dictionary containing flow summary information
    """
    if not spans:
        return {}

    # Sort by start time
    sorted_spans = sorted(spans, key=lambda s: s.get("startTimeUnixNano", s.get("start_time", 0)))

    # Get root span (first span, typically)
    root_span = sorted_spans[0]

    # Extract key attributes
    attrs = root_span.get("attributes", {})
    if isinstance(attrs, list):
        attrs = parse_attributes(attrs)

    http_method = get_attr_value(root_span, ["http.method", "http.request.method"])
    http_route = get_attr_value(root_span, ["http.route", "http.target", "url.path"])
    status_code = get_attr_value(root_span, ["http.status_code", "http.response.status_code"])

    # Build service chain
    services = []
    for span in sorted_spans:
        service = span.get("serviceName", "unknown")
        if service not in services:
            services.append(service)

    return {
        "root_span_name": root_span.get("name", "unknown"),
        "root_service": root_span.get("serviceName", "unknown"),
        "span_count": len(spans),
        "service_chain": services,
        "http_method": http_method,
        "http_route": http_route,
        "status_code": status_code,
    }
