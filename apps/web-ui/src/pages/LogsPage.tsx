import { useState, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Card, Table, Badge, Alert, Button, Collapse } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { useLogsQuery } from '@/api/queries/useLogsQuery';
import { useAutoRefresh } from '@/hooks/useAutoRefresh';
import { useQuery } from '@/contexts/QueryContext';
import { formatTimestamp } from '@/utils/formatting';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { EmptyState } from '@/components/common/EmptyState';
import { NavigableTraceId } from '@/components/common/NavigableTraceId';
import { NavigableSpanId } from '@/components/common/NavigableSpanId';
import { TruncatedId } from '@/components/common/TruncatedId';
import { CopyButton } from '@/components/common/CopyButton';
import { CompactQueryBuilder } from '@/components/query/CompactQueryBuilder';
import { LOG_FIELD_SCHEMA } from '@/components/query/fieldSchemas';
import type { LogRecord } from '@/api/types/log';
import type { Filter } from '@/api/types/common';

export default function LogsPage() {
  const { t } = useTranslation();
  const location = useLocation();
  const { queryState, refreshTimeWindow, updateFilters } = useQuery();
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());

  // Apply initial filters from navigation state (e.g., from Service Catalog)
  useEffect(() => {
    const state = location.state as { initialFilters?: Filter[] } | null;
    if (state?.initialFilters) {
      updateFilters(state.initialFilters);
      // Clear the state to prevent reapplying filters on subsequent renders
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  const { data, isLoading, error, refetch } = useLogsQuery({
    time_range: queryState.timeRange,
    filters: queryState.filters,
    pagination: { limit: 100 },
  });

  // Auto-refresh with time window sliding
  useAutoRefresh(() => {
    refreshTimeWindow(); // Update time range if in live mode
    refetch();
  });

  const getSeverityBadge = (severity: string) => {
    const severityMap: Record<string, string> = {
      FATAL: 'danger',
      ERROR: 'danger',
      WARN: 'warning',
      WARNING: 'warning',
      INFO: 'info',
      DEBUG: 'secondary',
      TRACE: 'secondary',
    };
    const variant = severityMap[severity.toUpperCase()] || 'secondary';
    return <Badge bg={variant}>{severity}</Badge>;
  };

  const truncateBody = (body: string | Record<string, unknown>, maxLength = 100): string => {
    if (!body) return '-';
    const bodyStr: string = typeof body === 'string' ? body : JSON.stringify(body);
    if (bodyStr.length <= maxLength) return bodyStr;
    return bodyStr.substring(0, maxLength) + '...';
  };

  const getDisplayMessage = (log: LogRecord): string => {
    // Check if body is effectively empty
    const isEmpty =
      !log.body ||
      (typeof log.body === 'string' && (log.body.trim() === '' || log.body === '{}')) ||
      (typeof log.body === 'object' && Object.keys(log.body).length === 0);

    // If body has content, return it
    if (!isEmpty) {
      return truncateBody(log.body);
    }

    // If no body but has attributes, show simplified attributes JSON
    if (log.attributes && log.attributes.length > 0) {
      // Try to find any attributes (not just attributes.* prefixed ones)
      const simplified: Record<string, unknown> = {};
      const displayAttrs = log.attributes.slice(0, 3);
      displayAttrs.forEach(attr => {
        // Remove common prefixes for cleaner display
        let key = attr.key;
        if (key.startsWith('attributes.')) {
          key = key.replace('attributes.', '');
        }
        simplified[key] = attr.value;
      });
      if (Object.keys(simplified).length > 0) {
        return truncateBody(simplified, 100);
      }
    }

    return '-';
  };

  const toggleExpand = (index: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedRows(newExpanded);
  };

  return (
    <>
      {/* Compact Query Builder */}
      <CompactQueryBuilder fieldSchema={LOG_FIELD_SCHEMA} showFreeTextSearch={true} />

      {isLoading && <LoadingSpinner message={t('logs.loading', 'Loading logs...')} />}

      {error && (
        <Alert variant="danger">
          <Alert.Heading>{t('logs.errorLoading', 'Error loading logs')}</Alert.Heading>
          <p>{error instanceof Error ? error.message : t('errors.unknown', 'Unknown error')}</p>
        </Alert>
      )}

      {!isLoading && !error && (!data || !data.logs || data.logs.length === 0) && (
        <EmptyState
          title={t('logs.noLogs', 'No logs found')}
          description={t('logs.noLogsDesc', 'No logs match your current filters. Try adjusting your search criteria or wait for new logs to arrive.')}
        />
      )}

      {!isLoading && !error && data && data.logs && data.logs.length > 0 && (
        <Card>
          <Card.Header>
            <strong>{data.logs.length} logs</strong>
          </Card.Header>
          <Card.Body className="p-0">
            <Table hover responsive className="mb-0">
              <thead>
                <tr>
                  <th style={{ width: '50px' }}></th>
                  <th style={{ width: '140px' }}>{t('logs.timestamp', 'Timestamp')}</th>
                  <th style={{ width: '100px' }}>{t('logs.severity', 'Severity')}</th>
                  <th>{t('logs.eventData', 'Event Data')}</th>
                  <th style={{ width: '150px' }}>{t('logs.traceId', 'Trace ID')}</th>
                  <th style={{ width: '150px' }}>{t('logs.serviceName', 'Service')}</th>
                </tr>
              </thead>
              <tbody>
                {data.logs.map((log: LogRecord, index: number) => {
                  const isExpanded = expandedRows.has(index);
                  return (
                    <>
                      <tr key={`${log.timestamp}-${index}`}>
                        <td>
                          <Button
                            variant="link"
                            size="sm"
                            onClick={() => toggleExpand(index)}
                            className="p-0 text-decoration-none"
                          >
                            <i className={`bi bi-chevron-${isExpanded ? 'down' : 'right'}`}></i>
                          </Button>
                        </td>
                        <td className="small">{log.timestamp ? formatTimestamp(log.timestamp) : '-'}</td>
                        <td>{getSeverityBadge(log.severity_text || 'INFO')}</td>
                        <td>
                          <code className="small">{getDisplayMessage(log)}</code>
                        </td>
                        <td>
                          {log.trace_id ? (
                            <NavigableTraceId traceId={log.trace_id} showCopy={false} />
                          ) : (
                            <span className="text-muted">-</span>
                          )}
                        </td>
                        <td>
                          {log.service_name || '-'}
                          {log.service_namespace && (
                            <Badge bg="light" text="dark" className="ms-1 small">
                              {log.service_namespace}
                            </Badge>
                          )}
                        </td>
                      </tr>
                      <tr key={`${log.timestamp}-${index}-details`}>
                        <td colSpan={6} className="p-0 border-0">
                          <Collapse in={isExpanded}>
                            <div className="p-3 bg-light">
                              <div className="row">
                                <div className="col-md-6">
                                  <h6 className="mb-2">{t('logs.details', 'Log Details')}</h6>
                                  <table className="table table-sm table-borderless mb-3">
                                    <tbody>
                                      <tr>
                                        <td className="text-muted" style={{ width: '120px' }}>
                                          {t('logs.timestamp', 'Timestamp')}:
                                        </td>
                                        <td>{log.timestamp ? formatTimestamp(log.timestamp) : '-'}</td>
                                      </tr>
                                      <tr>
                                        <td className="text-muted">Severity:</td>
                                        <td>
                                          {getSeverityBadge(log.severity_text || 'INFO')}
                                          {log.severity_number !== undefined && (
                                            <span className="text-muted ms-2 small">({log.severity_number})</span>
                                          )}
                                        </td>
                                      </tr>
                                      <tr>
                                        <td className="text-muted">Trace ID:</td>
                                        <td>
                                          {log.trace_id ? (
                                            <div className="d-flex align-items-center gap-2">
                                              <TruncatedId id={log.trace_id} maxLength={24} />
                                              <NavigableTraceId traceId={log.trace_id} showCopy={false} />
                                            </div>
                                          ) : (
                                            <span className="text-muted">-</span>
                                          )}
                                        </td>
                                      </tr>
                                      <tr>
                                        <td className="text-muted">Span ID:</td>
                                        <td>
                                          {log.span_id && log.trace_id ? (
                                            <NavigableSpanId spanId={log.span_id} traceId={log.trace_id} />
                                          ) : log.span_id ? (
                                            <TruncatedId id={log.span_id} />
                                          ) : (
                                            <span className="text-muted">-</span>
                                          )}
                                        </td>
                                      </tr>
                                    </tbody>
                                  </table>

                                  <h6 className="mb-2">Service Info</h6>
                                  <table className="table table-sm table-borderless mb-0">
                                    <tbody>
                                      <tr>
                                        <td className="text-muted" style={{ width: '120px' }}>
                                          Service:
                                        </td>
                                        <td>{log.service_name || '-'}</td>
                                      </tr>
                                      {log.service_namespace && (
                                        <tr>
                                          <td className="text-muted">Namespace:</td>
                                          <td>{log.service_namespace}</td>
                                        </tr>
                                      )}
                                    </tbody>
                                  </table>
                                </div>

                                <div className="col-md-6">
                                  <h6 className="mb-2">Message Body</h6>
                                  <div className="bg-white p-2 rounded border" style={{ maxHeight: '300px', overflow: 'auto' }}>
                                    {typeof log.body === 'string' ? (
                                      <pre className="mb-0 small">{log.body}</pre>
                                    ) : (
                                      <pre className="mb-0 small">{JSON.stringify(log.body, null, 2)}</pre>
                                    )}
                                  </div>

                                  {log.attributes && Object.keys(log.attributes).length > 0 && (
                                    <>
                                      <h6 className="mb-2 mt-3">Attributes</h6>
                                      <div
                                        className="bg-white p-2 rounded border"
                                        style={{ maxHeight: '200px', overflow: 'auto' }}
                                      >
                                        <table className="table table-sm table-borderless mb-0">
                                          <tbody>
                                            {Object.entries(log.attributes).map(([key, value]) => (
                                              <tr key={key}>
                                                <td className="text-muted small" style={{ width: '40%' }}>
                                                  {key}
                                                </td>
                                                <td className="small">
                                                  <code>{typeof value === 'string' ? value : JSON.stringify(value)}</code>
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
