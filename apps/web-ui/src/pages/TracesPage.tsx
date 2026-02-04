import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Card, Table, Badge, Button, Alert } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { useTracesQuery } from '@/api/queries/useTracesQuery';
import { useAutoRefresh } from '@/hooks/useAutoRefresh';
import { useQuery } from '@/contexts/QueryContext';
import { formatTimestamp, formatDuration } from '@/utils/formatting';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { EmptyState } from '@/components/common/EmptyState';
import { TruncatedId } from '@/components/common/TruncatedId';
import { CompactQueryBuilder } from '@/components/query/CompactQueryBuilder';
import { TRACE_FIELD_SCHEMA } from '@/components/query/fieldSchemas';
import { TraceModal } from '@/components/trace/TraceModal';
import type { Trace } from '@/api/types/common';

export default function TracesPage() {
  const { t } = useTranslation();
  const { queryState, refreshTimeWindow } = useQuery();
  const location = useLocation();
  const [selectedTrace, setSelectedTrace] = useState<Trace | null>(null);

  const { data, isLoading, error, refetch } = useTracesQuery({
    time_range: queryState.timeRange,
    filters: queryState.filters,
    pagination: { limit: 50 },
  });

  // Auto-refresh with time window sliding
  useAutoRefresh(() => {
    refreshTimeWindow();
    refetch();
  });

  // Handle navigation from logs page - auto-open trace if filterTraceId in location state
  useEffect(() => {
    const state = location.state as { filterTraceId?: string; openSpanId?: string } | null;
    if (state?.filterTraceId && data?.traces) {
      const trace = data.traces.find((t) => t.trace_id === state.filterTraceId);
      if (trace) {
        setSelectedTrace(trace);
        // Note: openSpanId handling is now done internally by TraceModal
      }
    }
  }, [location.state, data]);

  const getStatusBadge = (code?: number) => {
    if (!code) return <Badge bg="secondary">{t('traces.status.unset', 'Unset')}</Badge>;
    const statuses: Record<number, { label: string; variant: string }> = {
      0: { label: t('traces.status.unset', 'Unset'), variant: 'secondary' },
      1: { label: t('traces.status.ok', 'OK'), variant: 'success' },
      2: { label: t('traces.status.error', 'Error'), variant: 'danger' },
    };
    const status = statuses[code] || { label: t('traces.status.unknown', 'Unknown'), variant: 'secondary' };
    return <Badge bg={status.variant}>{status.label}</Badge>;
  };

  return (
    <>
      {/* Compact Query Builder */}
      <CompactQueryBuilder fieldSchema={TRACE_FIELD_SCHEMA} showFreeTextSearch={true} />

      {error && (
        <Alert variant="danger">
          <Alert.Heading>{t('traces.errorLoading', 'Error loading traces')}</Alert.Heading>
          <p>{error instanceof Error ? error.message : t('errors.unknown', 'Unknown error')}</p>
        </Alert>
      )}

      {isLoading ? (
        <LoadingSpinner message={t('traces.loading', 'Loading traces...')} />
      ) : !data || data.traces.length === 0 ? (
        <EmptyState
          title={t('traces.noTraces', 'No traces found')}
          description={t('traces.noTracesDesc', 'No traces match your current filters. Try adjusting your search criteria or wait for new traces to arrive.')}
        />
      ) : (
        <Card>
          <Card.Body className="p-0">
            <Table hover responsive>
              <thead>
                <tr>
                  <th style={{ width: '180px' }}>{t('traces.traceId', 'Trace ID')}</th>
                  <th>{t('traces.serviceName', 'Service')}</th>
                  <th style={{ width: '80px' }}>{t('traces.method', 'Method')}</th>
                  <th>{t('traces.routeTarget', 'Route/Target')}</th>
                  <th style={{ width: '80px' }}>{t('traces.httpStatus', 'HTTP Status')}</th>
                  <th style={{ width: '80px' }}>{t('traces.spans', 'Spans')}</th>
                  <th style={{ width: '160px' }}>{t('traces.timestamp', 'Start Time')}</th>
                  <th style={{ width: '100px' }}>{t('traces.duration', 'Duration')}</th>
                  <th style={{ width: '100px' }}>{t('traces.status', 'Status')}</th>
                </tr>
              </thead>
              <tbody>
                {data.traces.map((trace: Trace) => {
                  const rootSpan = trace.spans[0];
                  return (
                    <tr
                      key={trace.trace_id}
                      style={{ cursor: 'pointer' }}
                      onClick={() => setSelectedTrace(trace)}
                    >
                      <td>
                        <TruncatedId id={trace.trace_id} showCopy={false} />
                      </td>
                      <td>
                        {trace.root_service_name || rootSpan?.service_name || t('traces.unknown', 'Unknown')}
                        {rootSpan?.service_namespace && (
                          <Badge bg="light" text="dark" className="ms-1 small">
                            {rootSpan.service_namespace}
                          </Badge>
                        )}
                      </td>
                      <td>
                        {trace.root_span_method ? (
                          <Badge bg="primary">{trace.root_span_method}</Badge>
                        ) : (
                          <span className="text-muted">-</span>
                        )}
                      </td>
                      <td className="small">
                        {trace.root_span_target || trace.root_span_route || trace.root_span_name || '-'}
                      </td>
                      <td>
                        {trace.root_span_status_code ? (
                          <Badge
                            bg={
                              trace.root_span_status_code >= 500
                                ? 'danger'
                                : trace.root_span_status_code >= 400
                                  ? 'warning'
                                  : trace.root_span_status_code >= 200 && trace.root_span_status_code < 300
                                    ? 'success'
                                    : 'secondary'
                            }
                          >
                            {trace.root_span_status_code}
                          </Badge>
                        ) : (
                          <span className="text-muted">-</span>
                        )}
                      </td>
                      <td>
                        <Badge bg="info">{trace.spans.length}</Badge>
                      </td>
                      <td className="small">
                        {trace.start_time ? formatTimestamp(trace.start_time) : '-'}
                      </td>
                      <td>
                        {trace.duration_seconds !== undefined
                          ? formatDuration(trace.duration_seconds)
                          : '-'}
                      </td>
                      <td>{getStatusBadge(rootSpan?.status?.code)}</td>
                    </tr>
                  );
                })}
              </tbody>
            </Table>
            {data && data.pagination.has_more && (
              <div className="text-center mt-3">
                <Button variant="outline-secondary" size="sm">
                  {t('common.loadMore', 'Load More')}
                </Button>
              </div>
            )}
          </Card.Body>
        </Card>
      )}

      {/* Trace Detail Modal */}
      <TraceModal
        trace={selectedTrace}
        onHide={() => setSelectedTrace(null)}
      />
    </>
  );
}
