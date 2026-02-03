import { useEffect, useState } from 'react';
import { Table, Badge, Alert, Button, Collapse } from 'react-bootstrap';
import { useLogsQuery } from '@/api/queries/useLogsQuery';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { EmptyState } from '@/components/common/EmptyState';
import { formatTimestamp } from '@/utils/formatting';
import { TruncatedId } from '@/components/common/TruncatedId';
import { CopyButton } from '@/components/common/CopyButton';
import { NavigableSpanId } from '@/components/common/NavigableSpanId';
import type { LogRecord } from '@/api/types/log';

interface CorrelatedLogsProps {
  traceId: string;
  timeRange: {
    start_time: string;
    end_time: string;
  };
}

export function CorrelatedLogs({ traceId, timeRange }: CorrelatedLogsProps) {
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());

  const { data, isLoading, error, refetch } = useLogsQuery(
    {
      time_range: timeRange,
      filters: [
        {
          field: 'trace_id',
          operator: 'eq',
          value: traceId,
        },
      ],
      pagination: { limit: 100 },
    },
    {
      enabled: !!traceId,
      staleTime: 30000, // Cache for 30s
    }
  );

  useEffect(() => {
    if (traceId) {
      refetch();
    }
  }, [traceId, refetch]);

  const getSeverityBadge = (severity: string) => {
    const severityMap: Record<string, string> = {
      TRACE: 'secondary',
      DEBUG: 'info',
      INFO: 'primary',
      WARN: 'warning',
      ERROR: 'danger',
      FATAL: 'danger',
    };
    return <Badge bg={severityMap[severity] || 'secondary'}>{severity}</Badge>;
  };

  const truncateBody = (body: string | Record<string, unknown>, maxLength = 80): string => {
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
    if (log.attributes && log.attributes.length > 0) {
      // Try to find any attributes (not just attributes.* prefixed ones)
      const simplified: Record<string, unknown> = {};
      const displayAttrs = log.attributes.slice(0, 2);
      displayAttrs.forEach(attr => {
        // Remove common prefixes for cleaner display
        let key = attr.key;
        if (key.startsWith('attributes.')) {
          key = key.replace('attributes.', '');
        }
        simplified[key] = attr.value;
      });
      if (Object.keys(simplified).length > 0) {
        return truncateBody(simplified, 80);
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

  if (isLoading) {
    return <LoadingSpinner message="Loading correlated logs..." />;
  }

  if (error) {
    return (
      <Alert variant="warning">
        <Alert.Heading>Error loading logs</Alert.Heading>
        <p>{error instanceof Error ? error.message : 'Unknown error'}</p>
      </Alert>
    );
  }

  if (!data || data.logs.length === 0) {
    return (
      <EmptyState
        title="No correlated logs found"
        description="No logs found for this trace. Logs may not have been instrumented with trace context."
      />
    );
  }

  return (
    <div>
      <div className="mb-2">
        <Badge bg="info">{data.logs.length} correlated log{data.logs.length !== 1 ? 's' : ''}</Badge>
      </div>
      <div style={{ maxHeight: '400px', overflow: 'auto' }}>
        <Table hover size="sm" responsive>
          <thead className="sticky-top bg-white">
            <tr>
              <th style={{ width: '30px' }}></th>
              <th style={{ width: '160px' }}>Timestamp</th>
              <th style={{ width: '90px' }}>Severity</th>
              <th>Event Data</th>
              <th style={{ width: '130px' }}>Span ID</th>
              <th style={{ width: '110px' }}>Service</th>
            </tr>
          </thead>
          <tbody>
            {data.logs.map((log, index) => {
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
                    <td className="small">{formatTimestamp(log.timestamp)}</td>
                    <td>{getSeverityBadge(log.severity_text || 'INFO')}</td>
                    <td className="small">
                      <code className="small">{getDisplayMessage(log)}</code>
                    </td>
                    <td>
                      {log.span_id && traceId ? (
                        <NavigableSpanId spanId={log.span_id} traceId={traceId} maxLength={10} showCopy={false} />
                      ) : log.span_id ? (
                        <TruncatedId id={log.span_id} maxLength={10} showCopy={false} />
                      ) : (
                        <span className="text-muted">-</span>
                      )}
                    </td>
                    <td className="small">{log.service_name || '-'}</td>
                  </tr>
                  <tr key={`${log.timestamp}-${index}-details`}>
                    <td colSpan={6} className="p-0 border-0">
                      <Collapse in={isExpanded}>
                        <div className="p-2 bg-light">
                          <div className="row">
                            <div className="col-md-6">
                              <h6 className="mb-2 small">Log Details</h6>
                              <table className="table table-sm table-borderless mb-2">
                                <tbody>
                                  <tr>
                                    <td className="text-muted small" style={{ width: '100px' }}>
                                      Severity:
                                    </td>
                                    <td>
                                      {getSeverityBadge(log.severity_text || 'INFO')}
                                      {log.severity_number !== undefined && (
                                        <span className="text-muted ms-2 small">({log.severity_number})</span>
                                      )}
                                    </td>
                                  </tr>
                                  <tr>
                                    <td className="text-muted small">Span ID:</td>
                                    <td>
                                      {log.span_id && traceId ? (
                                        <NavigableSpanId spanId={log.span_id} traceId={traceId} maxLength={20} />
                                      ) : log.span_id ? (
                                        <TruncatedId id={log.span_id} maxLength={20} />
                                      ) : (
                                        <span className="text-muted">-</span>
                                      )}
                                    </td>
                                  </tr>
                                  <tr>
                                    <td className="text-muted small">Service:</td>
                                    <td className="small">{log.service_name || '-'}</td>
                                  </tr>
                                </tbody>
                              </table>
                            </div>

                            <div className="col-md-6">
                              <h6 className="mb-2 small">Message Body</h6>
                              <div
                                className="bg-white p-2 rounded border"
                                style={{ maxHeight: '150px', overflow: 'auto' }}
                              >
                                {typeof log.body === 'string' ? (
                                  <pre className="mb-0 small">{log.body}</pre>
                                ) : log.body ? (
                                  <pre className="mb-0 small">{JSON.stringify(log.body, null, 2)}</pre>
                                ) : (
                                  <span className="text-muted small">No message body</span>
                                )}
                              </div>

                              {log.attributes && log.attributes.length > 0 && (
                                <>
                                  <h6 className="mb-2 mt-2 small">Attributes</h6>
                                  <div
                                    className="bg-white p-2 rounded border"
                                    style={{ maxHeight: '120px', overflow: 'auto' }}
                                  >
                                    <table className="table table-sm table-borderless mb-0">
                                      <tbody>
                                        {log.attributes.map((attr, idx) => (
                                          <tr key={`${attr.key}-${idx}`}>
                                            <td className="text-muted small" style={{ width: '35%' }}>
                                              {attr.key}
                                            </td>
                                            <td className="small">
                                              <code className="small">
                                                {typeof attr.value === 'string' ? attr.value : JSON.stringify(attr.value)}
                                              </code>
                                              <CopyButton
                                                text={typeof attr.value === 'string' ? attr.value : JSON.stringify(attr.value)}
                                                className="ms-1"
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
      </div>
    </div>
  );
}
