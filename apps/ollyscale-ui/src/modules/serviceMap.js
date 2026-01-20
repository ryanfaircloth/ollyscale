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
let cy = null;

export function renderServiceMap(graph) {
    const container = document.getElementById('service-map-cy');
    if (!container) return;

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

    // Destroy existing Cytoscape instance if it exists
    if (cy) {
        cy.destroy();
        cy = null;
    }

    // Hide loading spinner
    const loadingEl = document.getElementById('map-loading');
    if (loadingEl) loadingEl.style.display = 'none';

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

    // Transform data for Cytoscape
    const elements = [];
                        graph.nodes.forEach(node => {
                            const inCount = incoming.get(node.id) || 0;
                            const outCount = outgoing.get(node.id) || 0;
                            let nodeType = (node.type || '').toLowerCase();
                            // Infer type if not set
                            if (!nodeType) {
                                if (inCount === 0 && outCount === 0) nodeType = 'isolated';
                                else nodeType = 'service';
                            }
                            let { shape, color, label } = getNodeTypeInfo(nodeType);
                            // Health coloring overrides
                            const metrics = node.metrics || {};
                            if (metrics.error_rate && metrics.error_rate > 5) {
                                color = '#ef4444';
                            } else if (metrics.error_rate && metrics.error_rate > 0) {
                                color = '#f59e0b';
                            }
                            elements.push({
                                group: 'nodes',
                                data: {
                                    id: node.id,
                                    label: node.label,
                                    shape: shape,
                                    type: label,
                                    color: color,
                                    metrics: metrics
                                }
                            });
                        });

    // Edges
    if (graph.edges && Array.isArray(graph.edges)) {
        graph.edges.forEach(edge => {
            elements.push({
                group: 'edges',
                data: {
                    id: `${edge.source}-${edge.target}`,
                    source: edge.source,
                    target: edge.target,
                    label: edge.p95 ? `${edge.p95}ms` : '',
                    p95: edge.p95,
                    weight: edge.value
                }
            });
        });
    }

    // If we already have a cytoscape instance, perform incremental update
    if (cy) {
        cy.batch(() => {
            const currentNodes = new Set(cy.nodes().map(n => n.id()));
            const currentEdges = new Set(cy.edges().map(e => e.id()));

            // Update Nodes
            elements.filter(e => e.group === 'nodes').forEach(ele => {
                if (currentNodes.has(ele.data.id)) {
                    cy.$id(ele.data.id).data(ele.data);
                    currentNodes.delete(ele.data.id);
                } else {
                    cy.add(ele);
                }
            });

            // Update Edges
            elements.filter(e => e.group === 'edges').forEach(ele => {
                if (currentEdges.has(ele.data.id)) {
                    cy.$id(ele.data.id).data(ele.data);
                    currentEdges.delete(ele.data.id);
                } else {
                    cy.add(ele);
                }
            });

            // Remove orphans
            currentNodes.forEach(nodeId => cy.$id(nodeId).remove());
            currentEdges.forEach(edgeId => cy.$id(edgeId).remove());
        });
        return;
    }

    // Initialize Cytoscape (First Load)
    cy = cytoscape({
        container: container,
        elements: elements,
        style: [
            {
                selector: 'node',
                style: {
                    'background-color': 'data(color)',
                    'label': 'data(label)',
                    'shape': 'data(shape)',
                    'color': '#64748b',
                    'font-size': '12px',
                    'font-family': 'Inter, sans-serif',
                    'font-weight': '600',
                    'text-valign': 'bottom',
                    'text-margin-y': 8,
                    'width': 40,
                    'height': 40,
                    'border-width': 2,
                    'border-color': '#ffffff',
                    'overlay-opacity': 0,
                    'transition-property': 'background-color, width, height',
                    'transition-duration': '0.3s'
                }
            },
            {
                selector: 'edge',
                style: {
                    'width': 2,
                    'line-color': '#cbd5e1',
                    'target-arrow-color': '#cbd5e1',
                    'target-arrow-shape': 'triangle',
                    'curve-style': 'bezier',
                    'label': 'data(label)',
                    'font-size': '10px',
                    'color': '#64748b',
                    'text-background-opacity': 1,
                    'text-background-color': '#ffffff',
                    'text-background-padding': 2,
                    'text-background-shape': 'roundrectangle',
                    'text-border-width': 1,
                    'text-border-color': '#e2e8f0',
                    'text-border-opacity': 1
                }
            },
            {
                selector: 'node:selected',
                style: {
                    'border-width': 4,
                    'border-color': '#bfdbfe'
                }
            }
        ],
        layout: {
            name: 'breadthfirst',
            directed: true,
            padding: 40,
            spacingFactor: 1.2,
            animate: true,
            avoidOverlap: true,
            circle: false,
            grid: false,
            roots: graph.nodes.length ? [graph.nodes[0].id] : [],
            // top-to-bottom orientation for clear edge direction
            orientation: 'vertical'
        },
        minZoom: 0.5,
        maxZoom: 3,
        wheelSensitivity: 0.2
    });

    // Click Handler for Details Panel
    cy.on('tap', 'node', function (evt) {
        const node = evt.target;
        const data = node.data();
        const metrics = data.metrics || {};

        const panel = document.getElementById('service-details-panel');
        const title = document.getElementById('details-title');
        const content = document.getElementById('details-content');

        if (!panel || !title || !content) return;

        title.textContent = data.label;

        let html = `
            <div style="margin-bottom: 8px; padding-bottom: 8px; border-bottom: 1px solid #f1f5f9;">
                <span style="background: ${data.color}; color: white; padding: 2px 6px; border-radius: 4px; font-size: 10px; text-transform: uppercase;">${data.type}</span>
            </div>
        `;

        if (metrics.span_count !== undefined) {
            html += `<div style="margin-bottom: 4px; display: flex; justify-content: space-between;"><span>Total Spans:</span> <strong>${metrics.span_count}</strong></div>`;
        }

        if (metrics.rate !== undefined && metrics.rate !== null) {
            html += `<div style="margin-bottom: 4px; display: flex; justify-content: space-between;"><span>Rate:</span> <strong>${metrics.rate} req/s</strong></div>`;
        }

        if (metrics.error_rate !== undefined && metrics.error_rate !== null) {
            const color = metrics.error_rate > 0 ? '#ef4444' : '#10b981';
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
        const safeLabel = data.label.replace(/'/g, "\\'");
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
        panel.style.display = 'block';
    });

    // Hide panel when clicking background
    cy.on('tap', function (evt) {
        if (evt.target === cy) {
            const panel = document.getElementById('service-details-panel');
            if (panel) panel.style.display = 'none';
        }
    });
}
