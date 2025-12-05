/**
 * API Module - Handles all backend API calls
 */
import { renderSpans, renderTraces, renderLogs, renderMetrics, renderServiceMap, renderStats } from './render.js';
import { renderServiceCatalog } from './serviceCatalog.js';
import { renderErrorState } from './utils.js';
import { filterTinyOllyData, filterTinyOllyTrace, filterTinyOllyMetric, filterTinyOllyMetricSeries } from './filter.js';

export async function loadStats() {
    try {
        const response = await fetch('/api/stats');
        const stats = await response.json();
        renderStats(stats);
    } catch (error) {
        console.error('Error loading stats:', error);
    }
}

export async function loadTraces() {
    try {
        const response = await fetch('/api/traces?limit=50');
        let traces = await response.json();

        // Filter out TinyOlly traces if hide toggle is active
        traces = traces.filter(filterTinyOllyTrace);

        renderTraces(traces);
    } catch (error) {
        console.error('Error loading traces:', error);
        document.getElementById('traces-container').innerHTML = renderErrorState('Error loading traces');
    }
}

export async function loadSpans(serviceName = null) {
    try {
        let url = '/api/spans?limit=50';
        if (serviceName) {
            url += `&service=${encodeURIComponent(serviceName)}`;
        }
        const response = await fetch(url);
        let spans = await response.json();

        // Filter out TinyOlly spans if hide toggle is active
        spans = spans.filter(filterTinyOllyData);

        renderSpans(spans);
    } catch (error) {
        console.error('Error loading spans:', error);
        document.getElementById('spans-container').innerHTML = renderErrorState('Error loading spans');
    }
}

export async function loadLogs(filterTraceId = null) {
    try {
        let url = '/api/logs?limit=100';
        if (filterTraceId) {
            url += `&trace_id=${filterTraceId}`;
        } else {
            const input = document.getElementById('trace-id-filter');
            if (input && input.value) {
                url += `&trace_id=${input.value.trim()}`;
            }
        }

        const response = await fetch(url);
        let logs = await response.json();

        // Filter out TinyOlly logs if hide toggle is active
        logs = logs.filter(filterTinyOllyData);

        renderLogs(logs, 'logs-container');
    } catch (error) {
        console.error('Error loading logs:', error);
        document.getElementById('logs-container').innerHTML = renderErrorState('Error loading logs');
    }
}

export async function loadMetrics() {
    try {
        const response = await fetch('/api/metrics');
        let metrics = await response.json();

        // Filter out TinyOlly metrics if hide toggle is active
        metrics = metrics.filter(filterTinyOllyMetric);

        renderMetrics(metrics);
    } catch (error) {
        console.error('Error loading metrics:', error);
    }
}

export async function loadServiceMap() {
    try {
        const response = await fetch('/api/service-map?limit=500');
        let graph = await response.json();

        // Filter out TinyOlly nodes and edges
        if (graph.nodes) {
            graph.nodes = graph.nodes.filter(filterTinyOllyData);
        }
        if (graph.edges) {
            graph.edges = graph.edges.filter(edge => {
                return edge.source !== 'tinyolly-ui' && edge.target !== 'tinyolly-ui';
            });
        }

        renderServiceMap(graph);
    } catch (error) {
        console.error('Error loading service map:', error);
    }
}

export async function fetchTraceDetail(traceId) {
    const response = await fetch(`/api/traces/${traceId}`);
    return await response.json();
}

export async function loadServiceCatalog() {
    try {
        const response = await fetch('/api/service-catalog');
        let services = await response.json();

        // Filter out TinyOlly service if hide toggle is active
        services = services.filter(filterTinyOllyData);

        renderServiceCatalog(services);
    } catch (error) {
        console.error('Error loading service catalog:', error);
        document.getElementById('catalog-container').innerHTML = renderErrorState('Error loading service catalog');
    }
}
