import { useState } from 'react';
import { Modal, Tabs, Tab, Card, Table, Badge, Button } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import { TruncatedId } from '@/components/common/TruncatedId';
import type { Filter } from '@/api/types/common';
import { DownloadButton } from '@/components/common/DownloadButton';
import { TraceWaterfall } from './TraceWaterfall';
import { SpanDetail } from './SpanDetail';
import { CorrelatedLogs } from './CorrelatedLogs';
import { formatTimestamp, formatDuration, formatAttributeValue } from '@/utils/formatting';
import type { Trace, Span } from '@/api/types/common';

interface TraceModalProps {
  trace: Trace | null;
  onHide: () => void;
}

const getStatusBadge = (statusCode?: number) => {
  if (statusCode === undefined || statusCode === null) return <Badge bg="secondary">Unknown</Badge>;
  if (statusCode === 0) return <Badge bg="secondary">Unset</Badge>;
  if (statusCode === 1) return <Badge bg="success">OK</Badge>;
  if (statusCode === 2) return <Badge bg="danger">Error</Badge>;
  return <Badge bg="secondary">Unknown</Badge>;
};

export function TraceModal({ trace, onHide }: TraceModalProps) {
  const [selectedSpan, setSelectedSpan] = useState<Span | null>(null);
  const navigate = useNavigate();

  const handleViewMetrics = () => {
    if (!trace?.root_service_name) return;
    const filters: Filter[] = [
      { field: 'resource.service.name', operator: 'eq', value: trace.root_service_name },
    ];
    navigate('/metrics', { state: { initialFilters: filters } });
    onHide();
  };

  return (
    <>
      <Modal show={!!trace} onHide={onHide} size="xl">
        <Modal.Header closeButton>
          <Modal.Title>
            Trace Details
            {trace && (
              <span className="ms-2">
                <TruncatedId id={trace.trace_id} maxLength={16} />
              </span>
            )}
          </Modal.Title>
        </Modal.Header>
        <Modal.Body>
          {trace && (
            <Tabs defaultActiveKey="waterfall" className="mb-3">
              <Tab eventKey="waterfall" title="Waterfall">
                <Card>
                  <Card.Body>
                    <TraceWaterfall
                      spans={trace.spans}
                      onSpanClick={setSelectedSpan}
                    />
                  </Card.Body>
                </Card>
              </Tab>
              <Tab eventKey="overview" title="Overview">
                <Card>
                  <Card.Body>
                    <div className="row">
                      <div className="col-md-6">
                        <div className="d-flex justify-content-between align-items-center mb-2">
                          <h6 className="mb-0">Trace Information</h6>
                          <Button
                            size="sm"
                            variant="outline-info"
                            onClick={handleViewMetrics}
                            title="View metrics for this service"
                          >
                            <i className="bi bi-graph-up me-1"></i>
                            View Metrics
                          </Button>
                        </div>
                        <dl className="row">
                          <dt className="col-sm-4">Trace ID:</dt>
                          <dd className="col-sm-8">
                            <TruncatedId id={trace.trace_id} maxLength={32} />
                          </dd>
                          <dt className="col-sm-4">Service:</dt>
                          <dd className="col-sm-8">
                            <Badge bg="info">{trace.root_service_name || 'Unknown'}</Badge>
                          </dd>
                          <dt className="col-sm-4">Start Time:</dt>
                          <dd className="col-sm-8">
                            {trace.start_time ? formatTimestamp(trace.start_time) : '-'}
                          </dd>
                          <dt className="col-sm-4">Duration:</dt>
                          <dd className="col-sm-8">
                            {trace.duration_seconds !== undefined
                              ? formatDuration(trace.duration_seconds)
                              : '-'}
                          </dd>
                          <dt className="col-sm-4">Span Count:</dt>
                          <dd className="col-sm-8">{trace.spans.length}</dd>
                          <dt className="col-sm-4">Status:</dt>
                          <dd className="col-sm-8">
                            {getStatusBadge(trace.spans[0]?.status?.code)}
                          </dd>
                        </dl>
                      </div>
                      <div className="col-md-6">
                        <h6>Root Span Attributes</h6>
                        {trace.spans[0]?.attributes && Object.keys(trace.spans[0].attributes).length > 0 ? (
                          <div style={{ maxHeight: '300px', overflow: 'auto' }}>
                            <dl className="row">
                              {Object.entries(trace.spans[0].attributes).map(([key, value]) => (
                                <div key={key} className="row mb-1">
                                  <dt className="col-sm-5 text-muted small">{key}:</dt>
                                  <dd className="col-sm-7 small" style={{ fontFamily: 'monospace', whiteSpace: 'pre-wrap' }}>{formatAttributeValue(value)}</dd>
                                </div>
                              ))}
                            </dl>
                          </div>
                        ) : (
                          <p className="text-muted">No attributes</p>
                        )}
                      </div>
                    </div>
                  </Card.Body>
                </Card>
              </Tab>
              <Tab eventKey="spans" title={`Spans (${trace.spans.length})`}>
                <Card>
                  <Card.Body>
                    <Table hover size="sm">
                      <thead>
                        <tr>
                          <th>Span Name</th>
                          <th>Service</th>
                          <th>Kind</th>
                          <th>Duration</th>
                          <th>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {trace.spans.map((span) => (
                          <tr key={span.span_id} style={{ cursor: 'pointer' }} onClick={() => setSelectedSpan(span)}>
                            <td>{span.name}</td>
                            <td>{span.service_name}</td>
                            <td>
                              <Badge bg="secondary" className="small">
                                {span.kind || 'UNSPECIFIED'}
                              </Badge>
                            </td>
                            <td className="small">
                              {span.duration_seconds !== undefined
                                ? formatDuration(span.duration_seconds)
                                : '-'}
                            </td>
                            <td>{getStatusBadge(span.status?.code)}</td>
                          </tr>
                        ))}
                      </tbody>
                    </Table>
                  </Card.Body>
                </Card>
              </Tab>
              <Tab eventKey="logs" title="Logs">
                <Card>
                  <Card.Body>
                    <CorrelatedLogs
                      traceId={trace.trace_id}
                      timeRange={{
                        start_time: trace.start_time || new Date(Date.now() - 3600000).toISOString(),
                        end_time: trace.end_time || new Date().toISOString(),
                      }}
                    />
                  </Card.Body>
                </Card>
              </Tab>
              <Tab eventKey="json" title="Raw JSON">
                <Card>
                  <Card.Body>
                    <div className="d-flex justify-content-end mb-2">
                      <DownloadButton data={trace} filename={`trace-${trace.trace_id}.json`} />
                    </div>
                    <pre
                      style={{
                        maxHeight: '500px',
                        overflow: 'auto',
                        backgroundColor: 'var(--app-surface)',
                        padding: '1rem',
                        borderRadius: '0.25rem',
                      }}
                    >
                      {JSON.stringify(trace, null, 2)}
                    </pre>
                  </Card.Body>
                </Card>
              </Tab>
            </Tabs>
          )}
        </Modal.Body>
      </Modal>

      {/* Span Detail Modal */}
      <SpanDetail
        span={selectedSpan}
        onHide={() => setSelectedSpan(null)}
        allSpans={trace?.spans || []}
        onLinkedSpanClick={(span) => setSelectedSpan(span)}
      />
    </>
  );
}
