import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Card, Table, Badge, Alert, Button, Collapse } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { useSpansQuery } from '@/api/queries/useSpansQuery';
import { useAutoRefresh } from '@/hooks/useAutoRefresh';
import { useQuery } from '@/contexts/QueryContext';
import { formatTimestamp, formatDuration } from '@/utils/formatting';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { EmptyState } from '@/components/common/EmptyState';
import { TruncatedId } from '@/components/common/TruncatedId';
import { CopyButton } from '@/components/common/CopyButton';
import { NavigableTraceId } from '@/components/common/NavigableTraceId';
import { CompactQueryBuilder } from '@/components/query/CompactQueryBuilder';
import { TRACE_FIELD_SCHEMA } from '@/components/query/fieldSchemas';
import type { Span } from '@/api/types/common';
import type { Filter } from '@/api/types/common';

export default function SpansPage() {
  const { t } = useTranslation();
  const location = useLocation();
  const { queryState, refreshTimeWindow, updateFilters } = useQuery();
  const [expandedRows, setExpandedRows] = useState<Set<string>>(new Set());

  // Apply initial filters from navigation state (e.g., from Service Catalog)
  useEffect(() => {
    const state = location.state as { initialFilters?: Filter[] } | null;
    if (state?.initialFilters) {
      updateFilters(state.initialFilters);
      // Clear the state to prevent reapplying filters on subsequent renders
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  const { data, isLoading, error, refetch } = useSpansQuery({
    time_range: queryState.timeRange,
    filters: queryState.filters,
    pagination: { limit: 100 },
  });

  // Auto-refresh with time window sliding
  useAutoRefresh(() => {
    refreshTimeWindow();
    refetch();
  });

  const getSpanKindBadge = (kind: number) => {
    const kinds = [
      t('spans.kinds.unspecified', 'Unspecified'),
      t('spans.kinds.internal', 'Internal'),
      t('spans.kinds.server', 'Server'),
      t('spans.kinds.client', 'Client'),
      t('spans.kinds.producer', 'Producer'),
      t('spans.kinds.consumer', 'Consumer')
    ];
    const colors = ['secondary', 'info', 'success', 'primary', 'warning', 'danger'];
    return <Badge bg={colors[kind] || 'secondary'}>{kinds[kind] || t('spans.kinds.unknown', 'Unknown')}</Badge>;
  };

  const getStatusBadge = (code?: number) => {
    if (!code) return <Badge bg="secondary">{t('spans.status.unset', 'Unset')}</Badge>;
    const statuses: Record<number, { label: string; variant: string }> = {
      0: { label: t('spans.status.unset', 'Unset'), variant: 'secondary' },
      1: { label: t('spans.status.ok', 'OK'), variant: 'success' },
      2: { label: t('spans.status.error', 'Error'), variant: 'danger' },
    };
    const status = statuses[code] || { label: t('spans.status.unknown', 'Unknown'), variant: 'secondary' };
    return <Badge bg={status.variant}>{status.label}</Badge>;
  };

  const getSpanKindLabel = (kind: number): string => {
    const kinds = [
      t('spans.kinds.unspecified', 'Unspecified'),
      t('spans.kinds.internal', 'Internal'),
      t('spans.kinds.server', 'Server'),
      t('spans.kinds.client', 'Client'),
      t('spans.kinds.producer', 'Producer'),
      t('spans.kinds.consumer', 'Consumer')
    ];
    return kinds[kind] || t('spans.kinds.unknown', 'Unknown');
  };

  const toggleExpand = (spanId: string) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(spanId)) {
      newExpanded.delete(spanId);
    } else {
      newExpanded.add(spanId);
    }
    setExpandedRows(newExpanded);
  };

  return (
    <>
      {/* Compact Query Builder */}
      <CompactQueryBuilder fieldSchema={TRACE_FIELD_SCHEMA} showFreeTextSearch={true} />

      {isLoading && <LoadingSpinner message={t('spans.loading', 'Loading spans...')} />}

      {error && (
        <Alert variant="danger">
          <Alert.Heading>{t('spans.errorLoading', 'Error loading spans')}</Alert.Heading>
          <p>{error instanceof Error ? error.message : t('errors.unknown', 'Unknown error')}</p>
        </Alert>
      )}

      {!isLoading && !error && (!data || !data.spans || data.spans.length === 0) && (
        <EmptyState
          title={t('spans.noSpans', 'No spans found')}
          description="No spans match your current filters. Try adjusting your search criteria or wait for new spans to arrive."
        />
      )}

      {!isLoading && !error && data && data.spans && data.spans.length > 0 && (
        <Card>
          <Card.Header>
            <strong>{data.spans.length} spans</strong>
          </Card.Header>
          <Card.Body className="p-0">
            <Table hover responsive className="mb-0">
              <thead>
                <tr>
                  <th style={{ width: '50px' }}></th>
                  <th>Span Name</th>
                  <th style={{ width: '100px' }}>Kind</th>
                  <th style={{ width: '150px' }}>Trace ID</th>
                  <th style={{ width: '150px' }}>Service</th>
                  <th style={{ width: '140px' }}>Start Time</th>
                  <th style={{ width: '100px' }}>Duration</th>
                  <th style={{ width: '90px' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {data.spans.map((span: Span) => {
                  const isExpanded = expandedRows.has(span.span_id);
                  return (
                    <>
                      <tr key={span.span_id}>
                        <td>
                          <Button
                            variant="link"
                            size="sm"
                            onClick={() => toggleExpand(span.span_id)}
                            className="p-0 text-decoration-none"
                          >
                            <i className={`bi bi-chevron-${isExpanded ? 'down' : 'right'}`}></i>
                          </Button>
                        </td>
                        <td>
                          <strong>{span.name || 'Unnamed Span'}</strong>
                        </td>
                        <td>{getSpanKindBadge(span.kind)}</td>
                        <td>
                          <NavigableTraceId traceId={span.trace_id} showCopy={false} />
                        </td>
                        <td>
                          {span.service_name || '-'}
                          {span.service_namespace && (
                            <Badge bg="light" text="dark" className="ms-1 small">
                              {span.service_namespace}
                            </Badge>
                          )}
                        </td>
                        <td className="small">{span.start_time ? formatTimestamp(span.start_time) : '-'}</td>
                        <td>
                          {span.duration_seconds !== undefined ? formatDuration(span.duration_seconds) : '-'}
                        </td>
                        <td>{getStatusBadge(span.status?.code)}</td>
                      </tr>
                      <tr key={`${span.span_id}-details`}>
                        <td colSpan={8} className="p-0 border-0">
                          <Collapse in={isExpanded}>
                            <div className="p-3 bg-light">
                              <div className="row">
                                <div className="col-md-6">
                                  <h6 className="mb-2">Span Details</h6>
                                  <table className="table table-sm table-borderless mb-3">
                                    <tbody>
                                      <tr>
                                        <td className="text-muted" style={{ width: '140px' }}>
                                          Span ID:
                                        </td>
                                        <td>
                                          <TruncatedId id={span.span_id} maxLength={24} />
                                        </td>
                                      </tr>
                                      <tr>
                                        <td className="text-muted">Trace ID:</td>
                                        <td>
                                          <div className="d-flex align-items-center gap-2">
                                            <TruncatedId id={span.trace_id} maxLength={24} />
                                            <NavigableTraceId traceId={span.trace_id} showCopy={false} />
                                          </div>
                                        </td>
                                      </tr>
                                      {span.parent_span_id && (
                                        <tr>
                                          <td className="text-muted">Parent Span ID:</td>
                                          <td>
                                            <TruncatedId id={span.parent_span_id} />
                                          </td>
                                        </tr>
                                      )}
                                      <tr>
                                        <td className="text-muted">Kind:</td>
                                        <td>
                                          {getSpanKindBadge(span.kind)}
                                          <span className="ms-2 text-muted small">({getSpanKindLabel(span.kind)})</span>
                                        </td>
                                      </tr>
                                      <tr>
                                        <td className="text-muted">Status:</td>
                                        <td>{getStatusBadge(span.status?.code)}</td>
                                      </tr>
                                      <tr>
                                        <td className="text-muted">Start Time:</td>
                                        <td>{span.start_time ? formatTimestamp(span.start_time) : '-'}</td>
                                      </tr>
                                      <tr>
                                        <td className="text-muted">Duration:</td>
                                        <td>
                                          {span.duration_seconds !== undefined
                                            ? formatDuration(span.duration_seconds)
                                            : '-'}
                                        </td>
                                      </tr>
                                    </tbody>
                                  </table>

                                  <h6 className="mb-2">Service</h6>
                                  <table className="table table-sm table-borderless mb-0">
                                    <tbody>
                                      <tr>
                                        <td className="text-muted" style={{ width: '140px' }}>
                                          Name:
                                        </td>
                                        <td>{span.service_name || '-'}</td>
                                      </tr>
                                      {span.service_namespace && (
                                        <tr>
                                          <td className="text-muted">Namespace:</td>
                                          <td>{span.service_namespace}</td>
                                        </tr>
                                      )}
                                    </tbody>
                                  </table>
                                </div>

                                <div className="col-md-6">
                                  {span.attributes && Object.keys(span.attributes).length > 0 && (
                                    <>
                                      <h6 className="mb-2">Attributes</h6>
                                      <div
                                        className="bg-white p-2 rounded border"
                                        style={{ maxHeight: '400px', overflow: 'auto' }}
                                      >
                                        <table className="table table-sm table-borderless mb-0">
                                          <tbody>
                                            {Object.entries(span.attributes).map(([key, value]) => (
                                              <tr key={key}>
                                                <td className="text-muted small" style={{ width: '40%' }}>
                                                  {key}
                                                </td>
                                                <td className="small">
                                                  <code>
                                                    {typeof value === 'string' ? value : JSON.stringify(value)}
                                                  </code>
                                                  <CopyButton
                                                    text={typeof value === 'string' ? value : JSON.stringify(value)}
                                                    className="ms-2"
                                                  />
                                                </td>
                                              </tr>
                                            ))}
                                          </tbody>
                                        </table>
                                      </div>
                                    </>
                                  )}

                                  {span.events && span.events.length > 0 && (
                                    <>
                                      <h6 className="mb-2 mt-3">Events ({span.events.length})</h6>
                                      <div
                                        className="bg-white p-2 rounded border"
                                        style={{ maxHeight: '200px', overflow: 'auto' }}
                                      >
                                        {span.events.map((event, idx) => (
                                          <div key={idx} className="mb-2 pb-2 border-bottom">
                                            <div className="small">
                                              <strong>{event.name}</strong>
                                              <div className="text-muted">
                                                {event.timestamp ? formatTimestamp(event.timestamp) : ''}
                                              </div>
                                              {event.attributes && Object.keys(event.attributes).length > 0 && (
                                                <div className="mt-1">
                                                  <code className="small">
                                                    {JSON.stringify(event.attributes, null, 2)}
                                                  </code>
                                                </div>
                                              )}
                                            </div>
                                          </div>
                                        ))}
                                      </div>
                                    </>
                                  )}
                                </div>
                              </div>
                            </div>
                          </Collapse>
                        </td>
                      </tr>
                    </>
                  );
                })}
              </tbody>
            </Table>
          </Card.Body>
        </Card>
      )}
    </>
  );
}
