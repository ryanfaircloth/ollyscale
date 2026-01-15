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
Tests for trace lint functionality.

These tests verify:
- Trace flow hash computation
- Identifier vs logic attribute distinction
- Lint rule detection (naming, auto-instrumentation, etc.)
- Flow summary generation
"""

import pytest

from common.trace_lint import compute_flow_summary, compute_trace_flow_hash, lint_trace


class TestTraceFlowHash:
    """Tests for trace flow hash computation."""

    def test_same_structure_same_hash(self):
        """Test that traces with same structure produce same hash."""
        spans1 = [
            {
                "name": "GET /api/users",
                "kind": 2,
                "serviceName": "frontend",
                "startTimeUnixNano": 1000,
                "attributes": [{"key": "http.method", "value": {"stringValue": "GET"}}],
                "status": {"code": 0},
            }
        ]

        spans2 = [
            {
                "name": "GET /api/users",
                "kind": 2,
                "serviceName": "frontend",
                "startTimeUnixNano": 2000,
                "attributes": [{"key": "http.method", "value": {"stringValue": "GET"}}],
                "status": {"code": 0},
            }
        ]

        hash1 = compute_trace_flow_hash(spans1)
        hash2 = compute_trace_flow_hash(spans2)

        assert hash1 == hash2, "Same structure should produce same hash"

    def test_different_identifiers_same_hash(self):
        """Test that different identifiers (IPs) produce same hash."""
        spans1 = [
            {
                "name": "GET /api/users",
                "kind": 2,
                "serviceName": "frontend",
                "startTimeUnixNano": 1000,
                "attributes": [
                    {"key": "http.method", "value": {"stringValue": "GET"}},
                    {"key": "net.peer.ip", "value": {"stringValue": "192.168.1.1"}},
                ],
                "status": {"code": 0},
            }
        ]

        spans2 = [
            {
                "name": "GET /api/users",
                "kind": 2,
                "serviceName": "frontend",
                "startTimeUnixNano": 2000,
                "attributes": [
                    {"key": "http.method", "value": {"stringValue": "GET"}},
                    {"key": "net.peer.ip", "value": {"stringValue": "10.0.0.5"}},
                ],
                "status": {"code": 0},
            }
        ]

        hash1 = compute_trace_flow_hash(spans1)
        hash2 = compute_trace_flow_hash(spans2)

        assert hash1 == hash2, "Different IPs should not affect flow hash"

    def test_different_status_different_hash(self):
        """Test that different status codes produce different hash."""
        spans1 = [
            {
                "name": "GET /api/users",
                "kind": 2,
                "serviceName": "frontend",
                "startTimeUnixNano": 1000,
                "attributes": [
                    {"key": "http.method", "value": {"stringValue": "GET"}},
                    {"key": "http.status_code", "value": {"intValue": 200}},
                ],
                "status": {"code": 0},
            }
        ]

        spans2 = [
            {
                "name": "GET /api/users",
                "kind": 2,
                "serviceName": "frontend",
                "startTimeUnixNano": 2000,
                "attributes": [
                    {"key": "http.method", "value": {"stringValue": "GET"}},
                    {"key": "http.status_code", "value": {"intValue": 500}},
                ],
                "status": {"code": 0},
            }
        ]

        hash1 = compute_trace_flow_hash(spans1)
        hash2 = compute_trace_flow_hash(spans2)

        assert hash1 != hash2, "Different status codes should produce different hash"


class TestLintRules:
    """Tests for lint rule detection."""

    def test_detect_attribute_naming_issue(self):
        """Test detection of underscore vs dot naming."""
        spans = [
            {
                "name": "GET /api/users",
                "kind": 2,
                "serviceName": "frontend",
                "startTimeUnixNano": 1000,
                "attributes": [
                    {"key": "http_method", "value": {"stringValue": "GET"}},  # Should be http.method
                ],
                "status": {"code": 0},
            }
        ]

        result = lint_trace(spans)
        findings = result.get("findings", [])

        assert len(findings) > 0, "Should detect naming issue"
        assert any(
            "http.method" in f["message"] for f in findings
        ), "Should suggest correct semantic convention"

    def test_detect_missing_http_method(self):
        """Test detection of missing HTTP method attribute."""
        spans = [
            {
                "name": "GET /api/users",  # Name suggests HTTP request
                "kind": 2,
                "serviceName": "frontend",
                "startTimeUnixNano": 1000,
                "attributes": [],  # Missing http.method
                "status": {"code": 0},
            }
        ]

        result = lint_trace(spans)
        findings = result.get("findings", [])

        assert len(findings) > 0, "Should detect missing http.method"
        assert any("http.method" in f["message"].lower() for f in findings), "Should mention http.method"

    def test_detect_missing_db_system(self):
        """Test detection of missing db.system attribute."""
        spans = [
            {
                "name": "SELECT * FROM users",  # Name suggests database operation
                "kind": 3,  # CLIENT
                "serviceName": "backend",
                "startTimeUnixNano": 1000,
                "attributes": [],  # Missing db.system
                "status": {"code": 0},
            }
        ]

        result = lint_trace(spans)
        findings = result.get("findings", [])

        assert len(findings) > 0, "Should detect missing db.system"
        assert any("db.system" in f["message"].lower() for f in findings), "Should mention db.system"

    def test_no_findings_for_correct_trace(self):
        """Test that well-formed traces produce no findings."""
        spans = [
            {
                "name": "GET /api/users",
                "kind": 2,
                "serviceName": "frontend",
                "startTimeUnixNano": 1000,
                "attributes": [
                    {"key": "http.method", "value": {"stringValue": "GET"}},
                    {"key": "http.status_code", "value": {"intValue": 200}},
                    {"key": "http.route", "value": {"stringValue": "/api/users"}},
                ],
                "status": {"code": 0},
            }
        ]

        result = lint_trace(spans)
        findings = result.get("findings", [])

        # May have info-level suggestions, but should not have errors or warnings
        errors_warnings = [f for f in findings if f["severity"] in ["error", "warning"]]
        assert len(errors_warnings) == 0, "Well-formed trace should not have errors or warnings"


class TestFlowSummary:
    """Tests for trace flow summary generation."""

    def test_compute_flow_summary(self):
        """Test flow summary computation."""
        spans = [
            {
                "name": "GET /api/users",
                "kind": 2,
                "serviceName": "frontend",
                "startTimeUnixNano": 1000,
                "attributes": [
                    {"key": "http.method", "value": {"stringValue": "GET"}},
                    {"key": "http.route", "value": {"stringValue": "/api/users"}},
                    {"key": "http.status_code", "value": {"intValue": 200}},
                ],
                "status": {"code": 0},
            },
            {
                "name": "database query",
                "kind": 3,
                "serviceName": "backend",
                "startTimeUnixNano": 1500,
                "attributes": [],
                "status": {"code": 0},
            },
        ]

        summary = compute_flow_summary(spans)

        assert summary["root_span_name"] == "GET /api/users"
        assert summary["root_service"] == "frontend"
        assert summary["span_count"] == 2
        assert summary["http_method"] == "GET"
        assert summary["http_route"] == "/api/users"
        assert summary["status_code"] == 200
        assert "frontend" in summary["service_chain"]
        assert "backend" in summary["service_chain"]

    def test_flow_summary_with_empty_spans(self):
        """Test flow summary with empty span list."""
        summary = compute_flow_summary([])
        assert summary == {}


class TestSeverityCounts:
    """Tests for severity counting in lint results."""

    def test_severity_counts(self):
        """Test that severity counts are computed correctly."""
        spans = [
            {
                "name": "GET /api/users",
                "kind": 2,
                "serviceName": "frontend",
                "startTimeUnixNano": 1000,
                "attributes": [
                    {"key": "http_method", "value": {"stringValue": "GET"}},  # Warning
                ],
                "status": {"code": 0},
            },
            {
                "name": "query",
                "kind": 3,
                "serviceName": "backend",
                "startTimeUnixNano": 1500,
                "attributes": [],  # Info for auto-instrumentation
                "status": {"code": 0},
            },
        ]

        result = lint_trace(spans)
        severity_counts = result.get("severity_counts", {})

        assert "error" in severity_counts
        assert "warning" in severity_counts
        assert "info" in severity_counts
        assert isinstance(severity_counts["error"], int)
        assert isinstance(severity_counts["warning"], int)
        assert isinstance(severity_counts["info"], int)
