import { useEffect, useRef, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import CytoscapeComponent from 'react-cytoscapejs';
import cytoscape from 'cytoscape';
import type { ServiceMapNode, ServiceMapEdge } from '@/api/types/service';
import { Button, ButtonGroup, Badge } from 'react-bootstrap';

interface ServiceGraphProps {
  nodes: ServiceMapNode[];
  edges: ServiceMapEdge[];
  layout: 'hierarchical' | 'grid';
}

export function ServiceGraph({ nodes, edges, layout }: ServiceGraphProps) {
  const navigate = useNavigate();
  const cyRef = useRef<cytoscape.Core | null>(null);
  const [selectedNode, setSelectedNode] = useState<ServiceMapNode | null>(null);

  // Get node shape for accessibility
  const getNodeShape = (type: string, hasEdges: boolean): string => {
    if (!hasEdges) return 'diamond'; // Isolated services

    switch (type) {
      case 'client':
        return 'rectangle';
      case 'server':
        return 'ellipse';
      case 'database':
        return 'hexagon';
      case 'messaging':
        return 'octagon';
      case 'external':
        return 'triangle';
      default:
        return 'ellipse';
    }
  };

  // Transform data to Cytoscape format
  const elements = [
    ...nodes.map(node => {
      const hasEdges = edges.some(e => e.source === node.id || e.target === node.id);
      const shape = getNodeShape(node.type, hasEdges);

      // Calculate error rate for health-based coloring
      const requestCount = node.metrics?.request_count || 0;
      const errorCount = node.metrics?.error_count || 0;
      const errorRate = requestCount > 0 ? (errorCount / requestCount) * 100 : 0;

      return {
        data: {
          id: node.id,
          label: node.name, // Just use the name without icon
          type: node.type || 'server',
          shape: shape,
          requestCount: requestCount,
          errorCount: errorCount,
          errorRate: errorRate,
          avgDuration: node.metrics ? node.metrics.p50_latency_ms / 1000 : 0,
          isolated: !hasEdges,
        },
      };
    }),
    ...edges.map((edge, idx) => {
      const avgLatency = edge.avg_latency_ms || 0;
      const callCount = edge.call_count || 0;

      return {
        data: {
          id: `edge-${idx}`,
          source: edge.source,
          target: edge.target,
          label: `${callCount.toLocaleString()} calls\n${avgLatency.toFixed(1)}ms avg`,
          callCount: callCount,
          avgLatency: avgLatency,
        },
      };
    }),
  ];

  // Color mapping for node types - theme-compatible colors with health-based overrides
  const getNodeColor = (type: string, isolated: boolean, errorRate?: number): string => {
    // Health-based coloring overrides (matches old UI behavior)
    if (errorRate !== undefined && errorRate > 5) {
      return '#ef4444'; // Red for high error rate (>5%)
    }
    if (errorRate !== undefined && errorRate > 0) {
      return '#f59e0b'; // Amber for any errors (>0%)
    }

    if (isolated) {
      return '#6c757d'; // Gray for isolated nodes
    }

    switch (type) {
      case 'client':
        return '#3b82f6'; // Bright blue - visible on light/dark
      case 'server':
        return '#10b981'; // Emerald green - visible on light/dark
      case 'database':
        return '#06b6d4'; // Cyan - visible on light/dark
      case 'messaging':
        return '#f59e0b'; // Amber - visible on light/dark
      case 'external':
        return '#ef4444'; // Red - visible on light/dark
      default:
        return '#10b981'; // Green (default to server)
    }
  };

  // Cytoscape stylesheet
  const stylesheet: any[] = [
    {
      selector: 'node',
      style: {
        // Use data attribute for label (computed during element creation)
        label: 'data(label)' as any,

        // Dynamic shape for accessibility
        shape: 'data(shape)' as any,

        // Dynamic color based on type, isolated state, and error rate
        'background-color': (ele: cytoscape.NodeSingular) =>
          getNodeColor(
            ele.data('type') as string,
            ele.data('isolated') as boolean,
            ele.data('errorRate') as number | undefined
          ) as any,

        // Label positioned below node
        'text-valign': 'bottom' as any,
        'text-halign': 'center' as any,
        'text-margin-y': 10 as any, // Space between node and label

        // Text styling - simple, no background shadow
        color: '#333' as any,
        'font-size': '13px' as any,
        'font-weight': '600' as any,
        'font-family': '-apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Helvetica", "Arial", sans-serif',

        // Node sizing
        width: 80 as any,
        height: 80 as any,
        'border-width': 2 as any,
        'border-color': '#fff' as any,
        'border-style': 'solid' as any,

        // Text wrapping
        'text-wrap': 'wrap' as any,
        'text-max-width': 120 as any,
      },
    },
    {
      selector: 'node[isolated]',
      style: {
        opacity: 0.6 as any, // Make isolated nodes more transparent (no border)
      },
    },
    {
      selector: 'node:selected',
      style: {
        'border-width': 3 as any,
        'border-color': '#ff6b6b' as any,
        'border-style': 'solid' as any,
      },
    },
    {
      selector: 'edge',
      style: {
        width: 2 as any,
        'line-color': '#999' as any,
        'target-arrow-color': '#999' as any,
        'target-arrow-shape': 'triangle' as any,
        'curve-style': 'bezier' as any,

        // Enhanced label with metrics and units
        label: 'data(label)' as any,
        'font-size': '10px' as any,
        'font-family': '-apple-system, BlinkMacSystemFont, "Segoe UI", "Roboto", "Helvetica", "Arial", sans-serif',
        color: '#333' as any,
        'text-background-color': '#fff' as any,
        'text-background-opacity': 0.9 as any,
        'text-background-padding': '3px' as any,
        'text-background-shape': 'roundrectangle' as any,
        'text-border-width': 1 as any,
        'text-border-color': '#ddd' as any,
        'text-border-opacity': 0.8 as any,
        'text-wrap': 'wrap' as any,
        'text-max-width': '120px' as any, // Increased from 80px to prevent truncation
      },
    },
    {
      selector: 'edge[callCount > 100]',
      style: {
        width: 4 as any,
        'line-color': '#0d6efd' as any,
        'target-arrow-color': '#0d6efd' as any,
      },
    },
    {
      selector: 'edge[callCount > 1000]',
      style: {
        width: 6 as any,
        'line-color': '#198754' as any,
        'target-arrow-color': '#198754' as any,
      },
    },
  ];

  // Layout configurations
  const getLayoutConfig = () => {
    if (layout === 'hierarchical') {
      return {
        name: 'breadthfirst',
        directed: true,
        spacingFactor: 1.5,
        animate: true,
        animationDuration: 500,
      };
    }
    return {
      name: 'grid',
      animate: true,
      animationDuration: 500,
      avoidOverlap: true,
      padding: 30,
    };
  };

  // Handle node selection
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;

    const handleTap = (evt: cytoscape.EventObject) => {
      const target = evt.target;
      if (target === cy) {
        setSelectedNode(null);
      } else if (target.isNode && target.isNode()) {
        const nodeData = target.data();
        const node = nodes.find(n => n.id === nodeData.id);
        setSelectedNode(node || null);
      }
    };

    cy.on('tap', handleTap);
    return () => {
      cy.off('tap', handleTap);
    };
  }, [nodes]);

  // Apply layout when layout prop changes
  useEffect(() => {
    const cy = cyRef.current;
    if (!cy) return;

    cy.layout(getLayoutConfig()).run();
  }, [layout]);

  // Control functions
  const handleZoomIn = () => cyRef.current?.zoom(cyRef.current.zoom() * 1.2);
  const handleZoomOut = () => cyRef.current?.zoom(cyRef.current.zoom() * 0.8);
  const handleFit = () => cyRef.current?.fit(undefined, 50);
  const handleCenter = () => cyRef.current?.center();

  return (
    <div style={{ position: 'relative', width: '100%', height: '100%', minHeight: '600px' }}>
      {/* Zoom controls */}
      <div style={{ position: 'absolute', top: 10, right: 10, zIndex: 1000 }}>
        <ButtonGroup vertical size="sm">
          <Button variant="light" onClick={handleZoomIn} title="Zoom In">
            <i className="bi bi-zoom-in"></i>
          </Button>
          <Button variant="light" onClick={handleZoomOut} title="Zoom Out">
            <i className="bi bi-zoom-out"></i>
          </Button>
          <Button variant="light" onClick={handleFit} title="Fit to Screen">
            <i className="bi bi-fullscreen"></i>
          </Button>
          <Button variant="light" onClick={handleCenter} title="Center">
            <i className="bi bi-bullseye"></i>
          </Button>
        </ButtonGroup>
      </div>

      {/* Selected node info */}
      {selectedNode && (
        <div
          className="card"
          style={{
            position: 'absolute',
            bottom: 10,
            left: 10,
            zIndex: 1000,
            maxWidth: 340,
          }}
        >
          <div className="card-body p-3">
            <div className="d-flex justify-content-between align-items-start mb-2">
              <h6 className="mb-0">{selectedNode.name}</h6>
              <button
                type="button"
                className="btn-close btn-sm"
                aria-label="Close"
                onClick={() => setSelectedNode(null)}
              ></button>
            </div>
            <div className="small">
              <div className="mb-2">
                <Badge bg={selectedNode.type === 'database' ? 'info' : 'success'}>
                  {selectedNode.type || 'server'}
                </Badge>
              </div>
              {selectedNode.metrics && (
                <>
                  {/* Span Count */}
                  {selectedNode.metrics.span_count !== undefined && (
                    <div className="d-flex justify-content-between mb-1">
                      <span>Total Spans:</span>
                      <strong>{selectedNode.metrics.span_count.toLocaleString()}</strong>
                    </div>
                  )}

                  {/* Rate (req/s) */}
                  {selectedNode.metrics.rate !== undefined && selectedNode.metrics.rate !== null && (
                    <div className="d-flex justify-content-between mb-1">
                      <span>Rate:</span>
                      <strong>{selectedNode.metrics.rate.toFixed(1)} req/s</strong>
                    </div>
                  )}

                  {/* Error Rate with color coding */}
                  {(() => {
                    const requestCount = selectedNode.metrics.request_count || 0;
                    const errorCount = selectedNode.metrics.error_count || 0;
                    const errorRate = requestCount > 0 ? (errorCount / requestCount) * 100 : 0;
                    const errorColor = errorRate > 5 ? '#ef4444' : errorRate > 0 ? '#f59e0b' : '#10b981';
                    return (
                      <div className="d-flex justify-content-between mb-1">
                        <span>Error Rate:</span>
                        <strong style={{ color: errorColor }}>{errorRate.toFixed(1)}%</strong>
                      </div>
                    );
                  })()}

                  {/* Latency grid (P50/P95/P99) */}
                  {selectedNode.metrics.p50_latency_ms !== undefined && (
                    <div className="mt-2">
                      <div className="fw-bold mb-1" style={{ color: '#334155' }}>Latency (ms)</div>
                      <div
                        className="d-grid gap-1"
                        style={{
                          gridTemplateColumns: '1fr 1fr 1fr',
                          background: '#f8fafc',
                          padding: '8px',
                          borderRadius: '4px',
                          textAlign: 'center',
                        }}
                      >
                        <div>
                          <div style={{ fontSize: '10px', color: '#64748b' }}>P50</div>
                          <div className="fw-bold">{selectedNode.metrics.p50_latency_ms.toFixed(1)}</div>
                        </div>
                        <div>
                          <div style={{ fontSize: '10px', color: '#64748b' }}>P95</div>
                          <div className="fw-bold">
                            {selectedNode.metrics.p95_latency_ms !== undefined
                              ? selectedNode.metrics.p95_latency_ms.toFixed(1)
                              : 'N/A'}
                          </div>
                        </div>
                        <div>
                          <div style={{ fontSize: '10px', color: '#64748b' }}>P99</div>
                          <div className="fw-bold">
                            {selectedNode.metrics.p99_latency_ms !== undefined
                              ? selectedNode.metrics.p99_latency_ms.toFixed(1)
                              : 'N/A'}
                          </div>
                        </div>
                      </div>
                    </div>
                  )}

                  {/* Navigation buttons */}
                  <div
                    className="mt-3 pt-2"
                    style={{ borderTop: '1px solid #f1f5f9' }}
                  >
                    <div className="d-flex gap-2 mb-2">
                      <Button
                        size="sm"
                        variant="primary"
                        className="flex-fill"
                        onClick={() => navigate(`/spans?service=${encodeURIComponent(selectedNode.name)}`)}
                      >
                        <i className="bi bi-diagram-3 me-1"></i>
                        Spans
                      </Button>
                      <Button
                        size="sm"
                        variant="primary"
                        className="flex-fill"
                        onClick={() => navigate(`/logs?service=${encodeURIComponent(selectedNode.name)}`)}
                      >
                        <i className="bi bi-journal-text me-1"></i>
                        Logs
                      </Button>
                    </div>
                    <Button
                      size="sm"
                      variant="primary"
                      className="w-100"
                      onClick={() => navigate(`/metrics?service=${encodeURIComponent(selectedNode.name)}`)}
                    >
                      <i className="bi bi-graph-up me-1"></i>
                      Metrics
                    </Button>
                  </div>
                </>
              )}
            </div>
          </div>
        </div>
      )}

      {/* Cytoscape graph */}
      <CytoscapeComponent
        elements={elements}
        stylesheet={stylesheet}
        layout={getLayoutConfig()}
        style={{ width: '100%', height: '100%' }}
        cy={(cy: cytoscape.Core) => {
          cyRef.current = cy;
        }}
      />
    </div>
  );
}
