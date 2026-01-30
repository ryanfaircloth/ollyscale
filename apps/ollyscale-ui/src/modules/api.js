/**
 * ollyScale v2 API Module
 *
 * Handles all backend API calls using POST-based search endpoints.
 * Copyright (c) 2026 Ryan Faircloth
 * AGPL-3.0 License
 */
import { renderSpans, renderTraces, renderLogs, renderMetrics, renderServiceMap } from './render.js';
import { renderServiceCatalog } from './serviceCatalog.js';
import { renderErrorState, renderLoadingState } from './utils.js';
import { getNamespaceFilters } from './namespaceFilter.js';
import { loadOpampStatus, initCollector } from './collector.js';

// ==================== API Helper Functions ====================

/**
 * Build a TimeRange for the last N minutes (ISO 8601 format)
 */
function buildTimeRange(minutes = 180) {
    const now = new Date();
    const start = new Date(now.getTime() - (minutes * 60 * 1000));
    return {
        start_time: start.toISOString(),
        end_time: now.toISOString()
    };
}

/**
 * Build a search request with time range, filters, and pagination
 * Automatically includes namespace filters from the namespace dropdown
 */
export function buildSearchRequest(additionalFilters = [], limit = 100, cursor = null) {
    // Get namespace filters (will be OR'd together)
    const namespaceFilters = getNamespaceFilters();
    console.log('[DEBUG buildSearchRequest] namespaceFilters:', namespaceFilters, 'type:', typeof namespaceFilters);

    // Combine filters: namespace group AND additional filters
    let allFilters = [];
    if (namespaceFilters && namespaceFilters.length > 0) {
        allFilters.push(...namespaceFilters);
    }
    if (additionalFilters.length > 0) {
        allFilters.push(...additionalFilters);
    }

    return {
        time_range: buildTimeRange(),
        filters: allFilters.length > 0 ? allFilters : null,
        pagination: {
            limit: limit,
            cursor: cursor
        }
    };
}

/**
 * POST request helper with JSON body
 */
async function postJSON(url, body) {
    const response = await fetch(url, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify(body)
    });

    if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    return await response.json();
}

// ==================== API Functions ====================

/**
 * Load recent traces using POST-based search
 */
export async function loadTraces() {
    try {
        const requestBody = buildSearchRequest([], 50);
        const result = await postJSON('/api/traces/search', requestBody);

        // V2 returns {traces: [...], pagination: {...}}
        const traces = result.traces || [];

        renderTraces(traces);
    } catch (error) {
        console.error('Error loading traces:', error);
        document.getElementById('traces-container').innerHTML = renderErrorState('Error loading traces');
    }
}

/**
 * Load recent spans using POST-based spans search endpoint
 */
export async function loadSpans(serviceName = null) {
    const container = document.getElementById('spans-container');
    if (!container) {
        console.error('Spans container not found');
        return;
    }

    container.innerHTML = renderLoadingState('Loading spans...');

    try {
        // Build filters
        const filters = [];
        if (serviceName) {
            filters.push({
                field: 'service_name',
                operator: 'equals',
                value: serviceName
            });
        }

        // Use dedicated spans search endpoint (respects namespace filters)
        const requestBody = buildSearchRequest(filters, 50);
        const result = await postJSON('/api/spans/search', requestBody);

        // V2 returns {spans: [...], pagination: {...}}
        const spans = result.spans || [];

        renderSpans(spans);
    } catch (error) {
        console.error('Error loading spans:', error);
        container.innerHTML = renderErrorState('Error loading spans: ' + error.message);
    }
}

/**
 * Load recent logs using POST-based search with optional trace_id filter
 */
export async function loadLogs(filterTraceId = null) {
    try {
        // Get trace ID from parameter or input field
        let traceId = filterTraceId;
        if (!traceId) {
            const input = document.getElementById('trace-id-filter');
            if (input && input.value) {
                traceId = input.value.trim();
            }
        }

        // Build filters
        const filters = [];
        if (traceId) {
            filters.push({
                field: 'trace_id',
                operator: 'eq',
                value: traceId
            });
        }

        const requestBody = buildSearchRequest(filters, 100);
        const result = await postJSON('/api/logs/search', requestBody);

        // V2 returns {logs: [...], pagination: {...}}
        const logs = result.logs || [];

        renderLogs(logs, 'logs-container');
    } catch (error) {
        console.error('Error loading logs:', error);
        document.getElementById('logs-container').innerHTML = renderErrorState('Error loading logs');
    }
}

/**
 * Load recent metrics using POST-based search
 */
export async function loadMetrics() {
    const metricsTab = document.getElementById('metrics-content');
    if (!metricsTab || !metricsTab.classList.contains('active')) {
        return;
    }

    try {
        const requestBody = buildSearchRequest([], 100);
        const result = await postJSON('/api/metrics/search', requestBody);

        // V2 returns {metrics: [...], pagination: {...}}
        const metrics = result.metrics || [];

        renderMetrics(metrics);
    } catch (error) {
        console.error('Error loading metrics:', error);
    }
}

/**
 * Load service dependency map using POST-based endpoint with namespace filters
 */
export async function loadServiceMap() {
    const loadingEl = document.getElementById('map-loading');
    if (loadingEl) loadingEl.style.display = 'flex';

    try {
        const requestBody = buildSearchRequest([], 1000); // Include namespace filters
        const result = await postJSON('/api/service-map', requestBody);

        // V2 returns {nodes: [...], edges: [...], time_range: {...}}
        // Transform nodes: add 'id' and 'label' properties from 'name' for dagre-d3
        const graph = {
            nodes: (result.nodes || []).map(node => ({
                ...node,
                id: node.name,      // dagre-d3 needs 'id'
                label: node.name    // dagre-d3 needs 'label' for display
            })),
            edges: result.edges || []
        };

        renderServiceMap(graph);
    } catch (error) {
        console.error('Error loading service map:', error);
        if (loadingEl) loadingEl.style.display = 'none';
    }
}

/**
 * Fetch detailed trace information by trace ID
 */
export async function fetchTraceDetail(traceId) {
    const response = await fetch(`/api/traces/${traceId}`);
    return await response.json();
}

/**
 * Load service catalog with RED metrics
 */
export async function loadServiceCatalog() {
    try {
        const requestBody = buildSearchRequest([], 1000); // Get all services with namespace filters
        const result = await postJSON('/api/services', requestBody);

        // V2 returns {services: [...], total_count: N}
        const services = result.services || [];

        renderServiceCatalog(services);
    } catch (error) {
        console.error('Error loading service catalog:', error);
        document.getElementById('catalog-container').innerHTML = renderErrorState('Error loading service catalog');
    }
}
