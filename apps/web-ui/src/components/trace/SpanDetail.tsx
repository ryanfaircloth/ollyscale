import { Modal, Tabs, Tab, Badge, Table, Button } from 'react-bootstrap';
import { useNavigate } from 'react-router-dom';
import type { Span, Filter } from '@/api/types/common';
import { formatTimestamp, formatDuration, formatAttributeValue } from '@/utils/formatting';
import { TruncatedId } from '@/components/common/TruncatedId';
import { CopyButton } from '@/components/common/CopyButton';

interface SpanDetailProps {
  span: Span | null;
  onHide: () => void;
  allSpans?: Span[]; // All spans in the trace for linked span lookup
  onLinkedSpanClick?: (span: Span) => void; // Callback when clicking a linked span
}

export function SpanDetail({ span, onHide, allSpans = [], onLinkedSpanClick }: SpanDetailProps) {
  const navigate = useNavigate();

  if (!span) return null;

  const handleViewMetrics = () => {
    if (!span?.service_name) return;
    const filters: Filter[] = [
      { field: 'resource.service.name', operator: 'eq', value: span.service_name },
    ];
    if (span.service_namespace) {
      filters.push({ field: 'resource.service.namespace', operator: 'eq', value: span.service_namespace });
    }
    navigate('/metrics', { state: { initialFilters: filters } });
    onHide();
  };

  // Helper to find a linked span in the current trace
  const findLinkedSpan = (spanId: string): Span | undefined => {
    return allSpans.find((s) => s.span_id === spanId);
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

  const getStatusBadge = (code?: number) => {
    if (!code) return <Badge bg="secondary">Unset</Badge>;
    const statuses: Record<number, { label: string; variant: string }> = {
      0: { label: 'Unset', variant: 'secondary' },
      1: { label: 'OK', variant: 'success' },
      2: { label: 'Error', variant: 'danger' },
    };
    const status = statuses[code] || { label: 'Unknown', variant: 'secondary' };
    return <Badge bg={status.variant}>{status.label}</Badge>;
  };

  return (
    <Modal show={!!span} onHide={onHide} size="lg">
      <Modal.Header closeButton>
        <Modal.Title>Span Details: {span.name}</Modal.Title>
      </Modal.Header>
      <Modal.Body>
        <Tabs defaultActiveKey="overview" className="mb-3">
          <Tab eventKey="overview" title="Overview">
            <div className="row">
              <div className="col-md-6">
                <div className="d-flex justify-content-between align-items-center mb-2">
                  <h6 className="mb-0">Span Information</h6>
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
                  <dt className="col-sm-5">Span ID:</dt>
                  <dd className="col-sm-7">
                    <TruncatedId id={span.span_id} maxLength={16} />
                  </dd>
                  <dt className="col-sm-5">Trace ID:</dt>
                  <dd className="col-sm-7">
                    <TruncatedId id={span.trace_id} maxLength={16} />
                  </dd>
                  {span.parent_span_id && (
                    <>
                      <dt className="col-sm-5">Parent Span ID:</dt>
                      <dd className="col-sm-7">
                        <TruncatedId id={span.parent_span_id} maxLength={16} />
                      </dd>
                    </>
                  )}
                  <dt className="col-sm-5">Service:</dt>
                  <dd className="col-sm-7">
                    <Badge bg="info">{span.service_name || 'Unknown'}</Badge>
                    {span.service_namespace && (
                      <Badge bg="light" text="dark" className="ms-1">
                        {span.service_namespace}
                      </Badge>
                    )}
                  </dd>
                  <dt className="col-sm-5">Kind:</dt>
                  <dd className="col-sm-7">
                    <Badge bg="secondary">{getSpanKindLabel(span.kind)}</Badge>
                  </dd>
                  <dt className="col-sm-5">Status:</dt>
                  <dd className="col-sm-7">
                    {getStatusBadge(span.status?.code)}
                    {span.status?.message && (
                      <div className="small text-muted mt-1">{span.status.message}</div>
                    )}
                  </dd>
                </dl>
              </div>
              <div className="col-md-6">
                <h6 className="mb-3">Timing</h6>
                <dl className="row">
                  <dt className="col-sm-5">Start Time:</dt>
                  <dd className="col-sm-7 small">{formatTimestamp(span.start_time)}</dd>
                  <dt className="col-sm-5">End Time:</dt>
                  <dd className="col-sm-7 small">{formatTimestamp(span.end_time)}</dd>
                  <dt className="col-sm-5">Duration:</dt>
                  <dd className="col-sm-7">
                    <Badge bg="primary">{formatDuration(span.duration_seconds)}</Badge>
                  </dd>
                </dl>
              </div>
            </div>
          </Tab>

          <Tab eventKey="attributes" title={`Attributes (${span.attributes ? Object.keys(span.attributes).length : 0})`}>
            {span.attributes && Object.keys(span.attributes).length > 0 ? (
              <div style={{ maxHeight: '400px', overflow: 'auto' }}>
                <Table hover size="sm" responsive>
                  <thead>
                    <tr>
                      <th style={{ width: '40%' }}>Key</th>
                      <th>Value</th>
                    </tr>
                  </thead>
                  <tbody>
                    {Object.entries(span.attributes).map(([key, value]) => (
                      <tr key={key}>
                        <td className="text-muted small font-monospace">{key}</td>
                        <td className="small">
                          <span className="font-monospace" style={{ whiteSpace: 'pre-wrap' }}>{formatAttributeValue(value)}</span>
                          <CopyButton text={formatAttributeValue(value)} size="sm" className="ms-2" />
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </div>
            ) : (
              <p className="text-muted">No attributes</p>
            )}
          </Tab>

          {span.events && span.events.length > 0 && (
            <Tab eventKey="events" title={`Events (${span.events.length})`}>
              <div style={{ maxHeight: '400px', overflow: 'auto' }}>
                <Table hover size="sm" responsive>
                  <thead>
                    <tr>
                      <th>Name</th>
                      <th>Timestamp</th>
                      <th>Attributes</th>
                    </tr>
                  </thead>
                  <tbody>
                    {span.events.map((event, index) => (
                      <tr key={index}>
                        <td className="small">{event.name}</td>
                        <td className="small">{formatTimestamp(event.timestamp)}</td>
                        <td className="small">
                          {event.attributes && event.attributes.length > 0 ? (
                            <details>
                              <summary style={{ cursor: 'pointer' }}>
                                {event.attributes.length} attribute{event.attributes.length !== 1 ? 's' : ''}
                              </summary>
                              <pre className="mt-2 small">{JSON.stringify(event.attributes, null, 2)}</pre>
                            </details>
                          ) : (
                            <span className="text-muted">None</span>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </div>
            </Tab>
          )}

          {span.links && span.links.length > 0 && (
            <Tab eventKey="links" title={`Links (${span.links.length})`}>
              <div style={{ maxHeight: '400px', overflow: 'auto' }}>
                <Table hover size="sm" responsive>
                  <thead>
                    <tr>
                      <th>Trace ID</th>
                      <th>Span ID</th>
                      <th style={{ width: '100px' }}>Status</th>
                      <th>Attributes</th>
                      <th style={{ width: '100px' }}>Action</th>
                    </tr>
                  </thead>
                  <tbody>
                    {span.links.map((link, index) => {
                      const linkedSpan = findLinkedSpan(link.span_id);
                      const isSameTrace = link.trace_id === span.trace_id;
                      return (
                        <tr key={index}>
                          <td>
                            <TruncatedId id={link.trace_id} maxLength={12} />
                            {isSameTrace && (
                              <Badge bg="light" text="dark" className="ms-1" style={{ fontSize: '9px' }}>
                                Same Trace
                              </Badge>
                            )}
                          </td>
                          <td>
                            <TruncatedId id={link.span_id} maxLength={12} />
                          </td>
                          <td>
                            {linkedSpan ? (
                              getStatusBadge(linkedSpan.status?.code)
                            ) : (
                              <span className="text-muted small">Unknown</span>
                            )}
                          </td>
                          <td className="small">
                            {link.attributes && link.attributes.length > 0 ? (
                              <details>
                                <summary style={{ cursor: 'pointer' }}>
                                  {link.attributes.length} attribute{link.attributes.length !== 1 ? 's' : ''}
                                </summary>
                                <pre className="mt-2 small">{JSON.stringify(link.attributes, null, 2)}</pre>
                              </details>
                            ) : (
                              <span className="text-muted">None</span>
                            )}
                          </td>
                          <td>
                            {linkedSpan && onLinkedSpanClick ? (
                              <button
                                className="btn btn-sm btn-outline-primary"
                                onClick={() => onLinkedSpanClick(linkedSpan)}
                                title="View linked span details"
                              >
                                <i className="bi bi-box-arrow-up-right me-1"></i>View
                              </button>
                            ) : isSameTrace ? (
                              <span className="text-muted small">Not found</span>
                            ) : (
                              <span className="text-muted small">Different trace</span>
                            )}
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </Table>
              </div>
            </Tab>
          )}

          {span.resource && Object.keys(span.resource).length > 0 && (
            <Tab eventKey="resource" title="Resource">
              <div style={{ maxHeight: '400px', overflow: 'auto' }}>
                <pre className="small">{JSON.stringify(span.resource, null, 2)}</pre>
              </div>
            </Tab>
          )}

          {span.scope && Object.keys(span.scope).length > 0 && (
            <Tab eventKey="scope" title="Scope">
              <div style={{ maxHeight: '400px', overflow: 'auto' }}>
                <pre className="small">{JSON.stringify(span.scope, null, 2)}</pre>
              </div>
            </Tab>
          )}
        </Tabs>
      </Modal.Body>
    </Modal>
  );
}
