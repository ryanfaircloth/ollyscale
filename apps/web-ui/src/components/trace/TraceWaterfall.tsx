import { useState } from 'react';
import { Badge } from 'react-bootstrap';
import type { Span } from '@/api/types/common';
import { formatDuration } from '@/utils/formatting';

interface TraceWaterfallProps {
  spans: Span[];
  onSpanClick?: (span: Span) => void;
}

interface SpanRow {
  span: Span;
  depth: number;
  offsetMs: number;
  durationMs: number;
  children: SpanRow[];
}

export function TraceWaterfall({ spans, onSpanClick }: TraceWaterfallProps) {
  const [hoveredSpanId, setHoveredSpanId] = useState<string | null>(null);

  // Build parent-child hierarchy
  const buildSpanTree = (): SpanRow[] => {
    if (spans.length === 0) return [];

    // Find trace start time (earliest span)
    const traceStartMs = Math.min(...spans.map((s) => new Date(s.start_time).getTime()));

    // Create map of spans by ID
    const spanMap = new Map<string, Span>();
    spans.forEach((span) => spanMap.set(span.span_id, span));

    // Build hierarchy
    const rootSpans: SpanRow[] = [];
    const childrenMap = new Map<string, SpanRow[]>();

    const createSpanRow = (span: Span, depth: number): SpanRow => {
      const startMs = new Date(span.start_time).getTime();
      const endMs = new Date(span.end_time).getTime();
      return {
        span,
        depth,
        offsetMs: startMs - traceStartMs,
        durationMs: endMs - startMs,
        children: [],
      };
    };

    // First pass: identify roots and group children
    spans.forEach((span) => {
      if (!span.parent_span_id) {
        rootSpans.push(createSpanRow(span, 0));
      } else {
        if (!childrenMap.has(span.parent_span_id)) {
          childrenMap.set(span.parent_span_id, []);
        }
        childrenMap.get(span.parent_span_id)!.push(createSpanRow(span, 0));
      }
    });

    // Second pass: recursively build tree
    const attachChildren = (row: SpanRow) => {
      const children = childrenMap.get(row.span.span_id) || [];
      children.forEach((child) => {
        child.depth = row.depth + 1;
        attachChildren(child);
      });
      row.children = children.sort((a, b) => a.offsetMs - b.offsetMs);
    };

    rootSpans.forEach(attachChildren);
    return rootSpans.sort((a, b) => a.offsetMs - b.offsetMs);
  };

  // Flatten tree for rendering
  const flattenTree = (rows: SpanRow[]): SpanRow[] => {
    const result: SpanRow[] = [];
    const traverse = (row: SpanRow) => {
      result.push(row);
      row.children.forEach(traverse);
    };
    rows.forEach(traverse);
    return result;
  };

  const spanTree = buildSpanTree();
  const flatSpans = flattenTree(spanTree);

  if (flatSpans.length === 0) {
    return <div className="text-muted">No spans to display</div>;
  }

  // Calculate total trace duration
  const traceDurationMs = Math.max(...flatSpans.map((row) => row.offsetMs + row.durationMs));

  // Span kind colors
  const getSpanKindColor = (kind: number) => {
    const colors: Record<number, string> = {
      0: '#6c757d', // UNSPECIFIED - gray
      1: '#0d6efd', // INTERNAL - blue
      2: '#198754', // SERVER - green
      3: '#fd7e14', // CLIENT - orange
      4: '#6f42c1', // PRODUCER - purple
      5: '#d63384', // CONSUMER - pink
    };
    return colors[kind] || colors[0];
  };

  const getSpanKindLabel = (kind: number) => {
    const labels: Record<number, string> = {
      0: 'UNSPECIFIED',
      1: 'INTERNAL',
      2: 'SERVER',
      3: 'CLIENT',
      4: 'PRODUCER',
      5: 'CONSUMER',
    };
    return labels[kind] || 'UNKNOWN';
  };

  // Layout constants
  const rowHeight = 32;
  const labelWidth = 300;
  const timelineWidth = 800;
  const marginTop = 30;
  const marginBottom = 20;
  const totalHeight = flatSpans.length * rowHeight + marginTop + marginBottom;

  // Calculate position and width for span bar
  const getBarPosition = (row: SpanRow) => {
    const left = (row.offsetMs / traceDurationMs) * timelineWidth;
    const width = Math.max(2, (row.durationMs / traceDurationMs) * timelineWidth);
    return { left, width };
  };

  return (
    <div className="trace-waterfall" style={{ overflowX: 'auto', overflowY: 'auto', maxHeight: '600px' }}>
      <svg width={labelWidth + timelineWidth + 50} height={totalHeight} style={{ display: 'block' }}>
        {/* Header - Time markers */}
        <g>
          <line x1={labelWidth} y1={marginTop - 10} x2={labelWidth + timelineWidth} y2={marginTop - 10} stroke="#dee2e6" />
          {[0, 0.25, 0.5, 0.75, 1].map((fraction) => {
            const x = labelWidth + fraction * timelineWidth;
            const timeMs = fraction * traceDurationMs;
            return (
              <g key={fraction}>
                <line x1={x} y1={marginTop - 10} x2={x} y2={marginTop - 5} stroke="#6c757d" />
                <text x={x} y={marginTop - 15} textAnchor="middle" fontSize="11" fill="#6c757d">
                  {formatDuration(timeMs / 1000)}
                </text>
              </g>
            );
          })}
        </g>

        {/* Span rows */}
        {flatSpans.map((row, index) => {
          const y = marginTop + index * rowHeight;
          const { left, width } = getBarPosition(row);
          const isHovered = hoveredSpanId === row.span.span_id;
          const hasError = row.span.status?.code === 2;

          return (
            <g key={row.span.span_id}>
              {/* Background */}
              <rect
                x={0}
                y={y}
                width={labelWidth + timelineWidth}
                height={rowHeight}
                fill={isHovered ? '#f8f9fa' : index % 2 === 0 ? '#ffffff' : '#fafbfc'}
                style={{ cursor: 'pointer' }}
                onMouseEnter={() => setHoveredSpanId(row.span.span_id)}
                onMouseLeave={() => setHoveredSpanId(null)}
                onClick={() => onSpanClick?.(row.span)}
              />

              {/* Span label */}
              <foreignObject x={row.depth * 16 + 5} y={y + 2} width={labelWidth - row.depth * 16 - 10} height={rowHeight - 4}>
                <div style={{ fontSize: '13px', lineHeight: `${rowHeight - 4}px`, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  <span style={{ fontWeight: isHovered ? 600 : 400 }} title={row.span.name}>
                    {row.span.name}
                  </span>
                  {hasError && (
                    <Badge bg="danger" className="ms-1" style={{ fontSize: '9px', padding: '1px 4px' }}>
                      ERROR
                    </Badge>
                  )}
                </div>
              </foreignObject>

              {/* Timeline grid line */}
              <line x1={labelWidth} y1={y} x2={labelWidth + timelineWidth} y2={y} stroke="#e9ecef" strokeWidth="1" />

              {/* Span bar */}
              <rect
                x={labelWidth + left}
                y={y + 4}
                width={width}
                height={rowHeight - 8}
                fill={hasError ? '#dc3545' : getSpanKindColor(row.span.kind)}
                opacity={isHovered ? 0.9 : 0.7}
                rx="2"
                style={{ cursor: 'pointer' }}
                onMouseEnter={() => setHoveredSpanId(row.span.span_id)}
                onMouseLeave={() => setHoveredSpanId(null)}
                onClick={() => onSpanClick?.(row.span)}
              >
                <title>
                  {row.span.name}
                  {'\n'}Duration: {formatDuration(row.durationMs / 1000)}
                  {'\n'}Kind: {getSpanKindLabel(row.span.kind)}
                  {row.span.service_name && `\nService: ${row.span.service_name}`}
                </title>
              </rect>

              {/* Duration label on bar (if wide enough) */}
              {width > 50 && (
                <text
                  x={labelWidth + left + width / 2}
                  y={y + rowHeight / 2 + 4}
                  textAnchor="middle"
                  fontSize="11"
                  fill="#ffffff"
                  fontWeight="500"
                  style={{ pointerEvents: 'none' }}
                >
                  {formatDuration(row.durationMs / 1000)}
                </text>
              )}
            </g>
          );
        })}

        {/* Vertical grid lines */}
        {[0.25, 0.5, 0.75].map((fraction) => {
          const x = labelWidth + fraction * timelineWidth;
          return (
            <line
              key={fraction}
              x1={x}
              y1={marginTop}
              x2={x}
              y2={totalHeight - marginBottom}
              stroke="#e9ecef"
              strokeWidth="1"
              strokeDasharray="2,2"
            />
          );
        })}
      </svg>

      {/* Legend */}
      <div className="d-flex flex-wrap gap-3 mt-3 px-2" style={{ fontSize: '12px' }}>
        <div className="d-flex align-items-center gap-1">
          <div style={{ width: '12px', height: '12px', backgroundColor: getSpanKindColor(2), borderRadius: '2px' }} />
          <span>SERVER</span>
        </div>
        <div className="d-flex align-items-center gap-1">
          <div style={{ width: '12px', height: '12px', backgroundColor: getSpanKindColor(3), borderRadius: '2px' }} />
          <span>CLIENT</span>
        </div>
        <div className="d-flex align-items-center gap-1">
          <div style={{ width: '12px', height: '12px', backgroundColor: getSpanKindColor(1), borderRadius: '2px' }} />
          <span>INTERNAL</span>
        </div>
        <div className="d-flex align-items-center gap-1">
          <div style={{ width: '12px', height: '12px', backgroundColor: getSpanKindColor(4), borderRadius: '2px' }} />
          <span>PRODUCER</span>
        </div>
        <div className="d-flex align-items-center gap-1">
          <div style={{ width: '12px', height: '12px', backgroundColor: getSpanKindColor(5), borderRadius: '2px' }} />
          <span>CONSUMER</span>
        </div>
        <div className="d-flex align-items-center gap-1">
          <div style={{ width: '12px', height: '12px', backgroundColor: '#dc3545', borderRadius: '2px' }} />
          <span>ERROR</span>
        </div>
      </div>
    </div>
  );
}
