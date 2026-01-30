/*
 * Copyright (c) 2026, Ryan Faircloth & ollyScale contributors
 * SPDX-License-Identifier: AGPL-3.0
 *
 * This file is part of ollyScale and is licensed under the AGPL-3.0 license.
 * See the LICENSE file in the project root for more information.
 */

/**
 * Service Map Module - Renders service dependency graph using Cytoscape.js
 */

import * as d3 from "d3";
import * as dagreD3 from "dagre-d3";

export function renderServiceMap(graph) {
    const container = document.getElementById("service-map-cy");
    if (!container) return;
    container.innerHTML = "";

    // Central node type/shape/color/label mapping (single source of truth)
    const NODE_TYPE_MAP = [
        {
            key: 'isolated',
            shape: 'diamond',
            color: '#6366f1', // Indigo
            label: 'Isolated',
            svg: `<svg width="18" height="18" viewBox="0 0 18 18"><polygon points="9,2 16,9 9,16 2,9" fill="#6366f1" stroke="#6366f1" stroke-width="2"/></svg>`
        },
        {
            key: 'service',
            shape: 'ellipse',
            color: '#0ea5e9', // Sky Blue
            label: 'Service',
            svg: `<svg width="18" height="18" viewBox="0 0 18 18"><ellipse cx="9" cy="9" rx="8" ry="8" fill="#0ea5e9" stroke="#0ea5e9" stroke-width="2"/></svg>`
        },
        {
            key: 'database',
            shape: 'rectangle',
            color: '#f59e42', // Amber
            label: 'Database',
            svg: `<svg width="18" height="18" viewBox="0 0 18 18"><rect x="3" y="3" width="12" height="12" rx="2" fill="#f59e42" stroke="#f59e42" stroke-width="2"/></svg>`
        },
        {
            key: 'messaging',
            shape: 'hexagon',
            color: '#10b981', // Emerald
            label: 'Messaging',
            svg: `<svg width="18" height="18" viewBox="0 0 18 18"><polygon points="9,2 16,6 16,12 9,16 2,12 2,6" fill="#10b981" stroke="#10b981" stroke-width="2"/></svg>`
        },
        {
            key: 'external',
            shape: 'triangle',
            color: '#f43f5e', // Rose
            label: 'External',
            svg: `<svg width="18" height="18" viewBox="0 0 18 18"><polygon points="9,2 16,16 2,16" fill="#f43f5e" stroke="#f43f5e" stroke-width="2"/></svg>`
        },
    ];

    function getNodeTypeInfo(type) {
        const t = (type || '').toLowerCase();
        return (
            NODE_TYPE_MAP.find(n => n.key === t) ||
            NODE_TYPE_MAP.find(n => n.key === 'service')
        );
    }

    // Use NODE_TYPE_MAP for legend
    const legendMap = NODE_TYPE_MAP;
    // Node rendering uses NODE_TYPE_MAP and getNodeTypeInfo
    // Remove all duplicate shape/color logic

    // Render legend
    const legendEl = document.getElementById('service-map-legend');
    if (legendEl) {
        let html = '<div class="service-map-legend-title">Legend</div>';
        legendMap.forEach(({ svg, label }) => {
            html += `<div class="service-map-legend-item" title="${label}">
                <span class="service-map-legend-shape-svg" aria-label="${label}" tabindex="0">${svg}</span>
                <span class="service-map-legend-label">${label}</span>
            </div>`;
        });
        legendEl.innerHTML = html;
    }

    // Validate graph data
    if (!graph || !graph.nodes || !Array.isArray(graph.nodes)) {
        console.error('Invalid graph data:', graph);
        container.innerHTML = '<div style="padding: 20px; text-align: center; color: var(--text-muted);">Invalid service map data</div>';
        return;
   }


    // Hide loading spinner
    const loadingEl = document.getElementById("map-loading");
    if (loadingEl) loadingEl.style.display = "none";

    // Calculate node types (Root, Leaf, Intermediate)
    const incoming = new Map();
    const outgoing = new Map();

    graph.nodes.forEach(n => {
        incoming.set(n.id, 0);
        outgoing.set(n.id, 0);
    });

    // Safely handle edges (might be empty or undefined)
    if (graph.edges && Array.isArray(graph.edges)) {
        graph.edges.forEach(e => {
            outgoing.set(e.source, (outgoing.get(e.source) || 0) + 1);
            incoming.set(e.target, (incoming.get(e.target) || 0) + 1);
        });
    }


    // --- Dagre-D3 Migration ---
    // Create Dagre-D3 graph
    // We want top-down for flow, but left-right for nodes at the same level (rank)
    // We'll assign a 'rank' to each node based on its distance from the root(s)
    // Nodes at the same rank will be laid out left-right
    // Dagre-D3 expects shape to be one of: 'rect', 'ellipse', 'circle', 'diamond', 'hexagon', 'triangle'
    // Map our custom shape names to dagre-d3 supported shapes
    function mapShape(shape) {
        switch (shape) {
            case 'rectangle': return 'rect';
            case 'ellipse': return 'ellipse';
            case 'diamond': return 'diamond';
            case 'hexagon': return 'hexagon';
            case 'triangle': return 'triangle';
            default: return 'ellipse';
        }
    }

    // Create Dagre-D3 graph
    const g = new dagreD3.graphlib.Graph().setGraph({
        rankdir: "TB", // Top-Bottom for flow
        nodesep: 40,
        ranksep: 80,
        marginx: 20,
        marginy: 20
    });

    // Helper: BFS to assign rank (level) to each node
    function assignRanks(nodes, edges) {
        const ranks = {};
        const visited = new Set();
        // Find roots (nodes with no incoming edges)
        const nodeIds = nodes.map(n => n.id);
        const incomingCounts = Object.fromEntries(nodeIds.map(id => [id, 0]));
        edges.forEach(e => {
            incomingCounts[e.target] = (incomingCounts[e.target] || 0) + 1;
        });
        const roots = nodeIds.filter(id => incomingCounts[id] === 0);
        // BFS from roots
        const queue = roots.map(id => ({ id, rank: 0 }));
        while (queue.length) {
            const { id, rank } = queue.shift();
            if (visited.has(id)) continue;
            visited.add(id);
            ranks[id] = rank;
            // Find children
            edges.filter(e => e.source === id).forEach(e => {
                queue.push({ id: e.target, rank: rank + 1 });
            });
        }
        // Fallback: assign rank 0 to any unvisited node
        nodeIds.forEach(id => {
            if (!(id in ranks)) ranks[id] = 0;
        });
        return ranks;
    }

    const ranks = assignRanks(graph.nodes, graph.edges || []);

    // Add nodes
    graph.nodes.forEach((node) => {
        const inCount = incoming.get(node.id) || 0;
        const outCount = outgoing.get(node.id) || 0;
        let nodeType = (node.type || "").toLowerCase();
        if (!nodeType) {
            if (inCount === 0 && outCount === 0) nodeType = "isolated";
            else nodeType = "service";
        }
        let { shape, color, label } = getNodeTypeInfo(nodeType);
        // Health coloring overrides
        const metrics = node.metrics || {};
        if (metrics.error_rate && metrics.error_rate > 5) {
            color = "#ef4444";
        } else if (metrics.error_rate && metrics.error_rate > 0) {
            color = "#f59e0b";
        }
        g.setNode(node.id, {
            label: node.name,  // Use name as display label
            shape: mapShape(shape),
            type: label,
            color: color,
            metrics: metrics,
            class: "service-map-node",
            style: `fill: ${color}; stroke: #fff; stroke-width: 2px;`,
            labelStyle: "font-weight:600; font-size:12px; font-family:Inter,sans-serif; fill:#334155;",
            rank: ranks[node.id]
        });
    });

    // Add edges
    if (graph.edges && Array.isArray(graph.edges)) {
        // Deduplicate edges by source-target pair
        const edgeMap = new Map();
        graph.edges.forEach((edge) => {
            const key = `${edge.source}__${edge.target}`;
            if (!edgeMap.has(key)) {
                edgeMap.set(key, { ...edge });
            } else {
                // Aggregate metrics if needed (e.g., max p95 latency)
                const existing = edgeMap.get(key);
                if (edge.p95 && (!existing.p95 || edge.p95 > existing.p95)) {
                    existing.p95 = edge.p95;
                }
                // Optionally aggregate other metrics here
            }
        });
        // Add only unique edges to the graph
        for (const edge of edgeMap.values()) {
            // Build label with call count and average duration
            let label = "";
            if (edge.call_count) {
                label += `${edge.call_count} calls`;
            }
            if (edge.avg_duration_ms) {
                label += label ? ` / ${edge.avg_duration_ms}ms` : `${edge.avg_duration_ms}ms`;
            }

            g.setEdge(edge.source, edge.target, {
                label: label,
                style: "stroke: #cbd5e1; stroke-width: 2px;", // Remove shadow
                arrowheadStyle: "fill: #cbd5e1;",
                weight: edge.value || edge.call_count || 1,
            });
        }
    }

    // For each rank, set left-right layout for nodes at the same rank
    // This is handled by Dagre-D3's default layout, but we can visually annotate or group if needed
    // Optionally, you can add custom x/y for nodes at the same rank for more control

    // Render with Dagre-D3
    const svg = d3.select(container)
        .append("svg")
        .attr("width", "100%")
        .attr("height", 600)
        .attr("role", "img")
        .attr("aria-label", "Service Dependency Map");

    const inner = svg.append("g");
    const render = new dagreD3.render();

        render(inner, g);

        // Fix Dagre-D3 double arrowhead/black infill bug

        d3.select(container)
            .selectAll("marker")
            .attr("fill", "#cbd5e1")
            .attr("stroke", "#cbd5e1");

        // Remove any black fill from edge paths
        d3.select(container)
            .selectAll(".edgePath path")
            .attr("fill", "none");

        // Force only one marker per edge to prevent double arrowheads
        d3.select(container)
            .selectAll('.edgePath path')
            .attr('marker-end', function() {
                // Find the first marker defined in the SVG and use it
                const svg = d3.select(container).select('svg');
                const marker = svg.select('marker').attr('id');
                return marker ? `url(#${marker})` : null;
            });

    // Center graph
    const graphWidth = g.graph().width || 800;
    const graphHeight = g.graph().height || 600;
    svg.attr("viewBox", `0 0 ${graphWidth} ${graphHeight}`);

    // Accessibility: Add title/desc
    svg.append("title").text("Service Dependency Map");
    svg.append("desc").text("Top-down flow for dependencies, left-right for parallel nodes at the same time/rank");

    // Click handler for details panel
    inner.selectAll(".service-map-node")
        .on("click", function (event, nodeId) {
            const nodeData = g.node(nodeId);
            const metrics = nodeData.metrics || {};
            const panel = document.getElementById("service-details-panel");
            const title = document.getElementById("details-title");
            const content = document.getElementById("details-content");
            if (!panel || !title || !content) return;
            title.textContent = nodeData.label;
            let html = `
                <div style="margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #f1f5f9;">
                    <span style="background: ${nodeData.color}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; text-transform: uppercase;">${nodeData.type}</span>
                </div>
            `;
            if (metrics.span_count !== undefined) {
                html += `<div style="margin-bottom: 4px; display: flex; justify-content: space-between;"><span>Total Spans:</span> <strong>${metrics.span_count}</strong></div>`;
            }
            if (metrics.rate !== undefined && metrics.rate !== null) {
                html += `<div style="margin-bottom: 4px; display: flex; justify-content: space-between;"><span>Rate:</span> <strong>${metrics.rate} req/s</strong></div>`;
            }
            if (metrics.error_rate !== undefined && metrics.error_rate !== null) {
                const color = metrics.error_rate > 0 ? "#ef4444" : "#10b981";
                html += `<div style="margin-bottom: 4px; display: flex; justify-content: space-between;"><span>Error Rate:</span> <strong style="color: ${color}">${metrics.error_rate}%</strong></div>`;
            }
            if (metrics.duration_p50) {
                html += `
                    <div style="margin-top: 12px; font-weight: 600; margin-bottom: 6px; color: #334155;">Latency (ms)</div>
                    <div style="display: grid; grid-template-columns: 1fr 1fr 1fr; gap: 4px; text-align: center; background: #f8fafc; padding: 8px; border-radius: 4px;">
                        <div>
                            <div style="font-size: 10px; color: #64748b;">P50</div>
                            <div style="font-weight: 600;">${metrics.duration_p50}</div>
                        </div>
                        <div>
                            <div style="font-size: 10px; color: #64748b;">P95</div>
                            <div style="font-weight: 600;">${metrics.duration_p95}</div>
                        </div>
                        <div>
                            <div style="font-size: 10px; color: #64748b;">P99</div>
                            <div style="font-weight: 600;">${metrics.duration_p99}</div>
                        </div>
                    </div>
                `;
            } else {
                html += `<div style="margin-top: 12px; color: #94a3b8; font-style: italic;">No latency data available</div>`;
            }
            // Add navigation buttons
            const safeLabel = nodeData.label.replace(/'/g, "\\'");
            html += `
                <div style="margin-top: 16px; padding-top: 12px; border-top: 1px solid #f1f5f9; display: flex; flex-direction: column; gap: 8px;">
                    <div style="display: flex; gap: 8px;">
                        <button onclick="window.viewServiceSpans('${safeLabel}');"
                            style="flex: 1; padding: 6px; background: var(--primary); color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 11px; font-weight: 500; display: flex; align-items: center; justify-content: center; gap: 4px; transition: all 0.2s;">
                            <span>Spans</span>
                        </button>
                        <button onclick="window.viewServiceLogs('${safeLabel}');"
                            style="flex: 1; padding: 6px; background: var(--primary); color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 11px; font-weight: 500; display: flex; align-items: center; justify-content: center; gap: 4px; transition: all 0.2s;">
                            <span>Logs</span>
                        </button>
                    </div>
                    <button onclick="window.viewMetricsForService('${safeLabel}');"
                        style="width: 100%; padding: 6px; background: var(--primary); color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 11px; font-weight: 500; transition: all 0.2s;">
                        <span>Metrics</span>
                    </button>
                </div>
            `;
            content.innerHTML = html;
            panel.style.display = "block";
        });

    // Hide panel when clicking background
    svg.on("click", function (event) {
        if (event.target === svg.node()) {
            const panel = document.getElementById("service-details-panel");
            if (panel) panel.style.display = "none";
        }
    });

    // Debug: Log graph data for troubleshooting
    console.log("Service Map Graph Data:", graph);
    // Debug: Log nodes and edges
    console.log("Nodes:", graph.nodes);
    console.log("Edges:", graph.edges);

    // Remove the empty data check hack, but keep the feature for true empty cases
    // Only show the message if graph.nodes and graph.edges are both present and truly empty
    if (Array.isArray(graph.nodes) && Array.isArray(graph.edges) && graph.nodes.length === 0 && graph.edges.length === 0) {
        container.innerHTML += '<div style="position:absolute;top:50%;left:50%;transform:translate(-50%,-50%);color:#94a3b8;font-size:18px;text-align:center;">No service map data available</div>';
        return;
    }

    // Remove edge shadow via CSS override for dagre-d3
    // Move this to CSS: Add to your main CSS file (e.g., serviceMap.css)
    // .service-map-cy svg .edgePath path {
    //     filter: none !important;
    //     stroke: #cbd5e1 !important;
    //     stroke-width: 2px !important;
    // }
}
