import { useState, useMemo } from "react";
import { Table, Badge, Button, Card, ButtonGroup } from "react-bootstrap";
import { useNavigate } from 'react-router-dom';
import { useTranslation } from 'react-i18next';
import { useServicesQuery } from "@/api/queries/useServicesQuery";
import { useAutoRefresh } from "@/hooks/useAutoRefresh";
import { useLocalStorage } from "@/hooks/useLocalStorage";
import { formatNumber, formatDuration } from "@/utils/formatting";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { EmptyState } from "@/components/common/EmptyState";
import type { Service } from "@/api/types/service";
import type { Filter } from '@/api/types/common';

export default function ServiceCatalogPage() {
  const { t } = useTranslation();
  const navigate = useNavigate();

  // Sort state with localStorage persistence
  const [sortConfig, setSortConfig] = useLocalStorage<{
    column: string;
    direction: 'asc' | 'desc';
  }>('service-catalog-sort', { column: 'name', direction: 'asc' });

  // Time range: last 30 minutes
  const [timeRange] = useState(() => {
    const now = new Date();
    const thirtyMinutesAgo = new Date(now.getTime() - 30 * 60 * 1000);
    return {
      start_time: thirtyMinutesAgo.toISOString(),
      end_time: now.toISOString(),
    };
  });

  const { data, isLoading, error, refetch } = useServicesQuery({
    time_range: timeRange,
    pagination: { limit: 100 },
  });

  // Auto-refresh
  useAutoRefresh(() => refetch());

  // Calculate time range duration in minutes for rate calculation
  const timeRangeDurationMinutes = Math.abs(
    (new Date(timeRange.end_time).getTime() - new Date(timeRange.start_time).getTime()) / (1000 * 60)
  );

  const calculateRequestRate = (requestCount: number): number => {
    if (timeRangeDurationMinutes === 0) return 0;
    return requestCount / timeRangeDurationMinutes;
  };

  // Handle column sorting
  const handleSort = (column: string) => {
    setSortConfig(prev => ({
      column,
      direction: prev.column === column && prev.direction === 'asc' ? 'desc' : 'asc',
    }));
  };

  // Sort services based on current sort configuration
  const sortedServices = useMemo(() => {
    if (!data?.services) return [];

    const sorted = [...data.services];
    sorted.sort((a, b) => {
      let aVal: string | number;
      let bVal: string | number;

      switch (sortConfig.column) {
        case 'name':
          aVal = a.name.toLowerCase();
          bVal = b.name.toLowerCase();
          break;
        case 'namespace':
          aVal = (a.namespace || '').toLowerCase();
          bVal = (b.namespace || '').toLowerCase();
          break;
        case 'rate':
          aVal = a.metrics?.request_count ? calculateRequestRate(a.metrics.request_count) : 0;
          bVal = b.metrics?.request_count ? calculateRequestRate(b.metrics.request_count) : 0;
          break;
        case 'error_rate':
          aVal = a.metrics?.error_rate ?? 0;
          bVal = b.metrics?.error_rate ?? 0;
          break;
        case 'p50':
          aVal = a.metrics?.p50_latency_ms ?? 0;
          bVal = b.metrics?.p50_latency_ms ?? 0;
          break;
        case 'p95':
          aVal = a.metrics?.p95_latency_ms ?? 0;
          bVal = b.metrics?.p95_latency_ms ?? 0;
          break;
        case 'p99':
          aVal = a.metrics?.p99_latency_ms ?? 0;
          bVal = b.metrics?.p99_latency_ms ?? 0;
          break;
        default:
          return 0;
      }

      if (typeof aVal === 'string' && typeof bVal === 'string') {
        return sortConfig.direction === 'asc'
          ? aVal.localeCompare(bVal)
          : bVal.localeCompare(aVal);
      }

      // Ensure numeric comparison
      const numA = typeof aVal === 'number' ? aVal : 0;
      const numB = typeof bVal === 'number' ? bVal : 0;
      return sortConfig.direction === 'asc' ? numA - numB : numB - numA;
    });

    return sorted;
  }, [data?.services, sortConfig, timeRangeDurationMinutes]);

  const handleViewSpans = (serviceName: string, namespace?: string) => {
    const filters: Filter[] = [
      { field: 'service_name', operator: 'eq', value: serviceName },
    ];
    if (namespace) {
      filters.push({ field: 'service_namespace', operator: 'eq', value: namespace });
    }
    navigate('/spans', { state: { initialFilters: filters } });
  };

  const handleViewLogs = (serviceName: string, namespace?: string) => {
    const filters: Filter[] = [
      { field: 'service_name', operator: 'eq', value: serviceName },
    ];
    if (namespace) {
      filters.push({ field: 'service_namespace', operator: 'eq', value: namespace });
    }
    navigate('/logs', { state: { initialFilters: filters } });
  };

  const handleViewMetrics = (serviceName: string, namespace?: string) => {
    const filters: Filter[] = [
      { field: 'resource.service.name', operator: 'eq', value: serviceName },
    ];
    if (namespace) {
      filters.push({ field: 'resource.service.namespace', operator: 'eq', value: namespace });
    }
    navigate('/metrics', { state: { initialFilters: filters } });
  };

  const getErrorRateBadge = (errorRate: number) => {
    if (errorRate === 0) return <Badge bg="success">0%</Badge>;
    if (errorRate < 1) return <Badge bg="warning">{errorRate.toFixed(2)}%</Badge>;
    return <Badge bg="danger">{errorRate.toFixed(2)}%</Badge>;
  };

  const getLatencyColor = (p95: number) => {
    if (p95 < 100) return "success";
    if (p95 < 500) return "warning";
    return "danger";
  };

  if (isLoading) {
    return <LoadingSpinner message={t('services.loading', 'Loading services...')} />;
  }

  if (error) {
    return (
      <Card bg="danger" text="white" className="m-3">
        <Card.Body>
          <Card.Title>{t('services.errorLoading', 'Error loading services')}</Card.Title>
          <Card.Text>{error instanceof Error ? error.message : t('errors.unknown', 'Unknown error')}</Card.Text>
        </Card.Body>
      </Card>
    );
  }

  if (!data || !data.services) {
    return <LoadingSpinner message={t('services.loading', 'Loading services...')} />;
  }

  const totalServices = data.services.length;

  if (totalServices === 0) {
    return (
      <EmptyState
        title={t('services.noServices', 'No services found')}
        description={t('services.noServicesDesc', 'No services have reported telemetry data. Deploy applications with OpenTelemetry instrumentation to see them here.')}
      />
    );
  }

  return (
    <div>
      <div className="d-flex justify-content-between align-items-center mb-3">
        <div className="text-muted">
          {t('services.showingCount', 'Showing {{count}} service with RED metrics (Rate, Errors, Duration)', { count: totalServices })}
        </div>
        <Button variant="outline-primary" size="sm" onClick={() => refetch()}>
          <i className="bi bi-arrow-clockwise me-1"></i>
          {t('common.refresh', 'Refresh')}
        </Button>
      </div>

      <Card>
        <Card.Body className="p-0">
          <Table hover responsive className="mb-0">
            <thead>
              <tr>
                <th onClick={() => handleSort('name')} style={{ cursor: 'pointer', userSelect: 'none' }}>
                  Service Name {sortConfig.column === 'name' && (
                    <i className={`bi bi-arrow-${sortConfig.direction === 'asc' ? 'up' : 'down'}`}></i>
                  )}
                </th>
                <th onClick={() => handleSort('namespace')} style={{ width: "150px", cursor: 'pointer', userSelect: 'none' }}>
                  Namespace {sortConfig.column === 'namespace' && (
                    <i className={`bi bi-arrow-${sortConfig.direction === 'asc' ? 'up' : 'down'}`}></i>
                  )}
                </th>
                <th onClick={() => handleSort('rate')} style={{ width: "120px", cursor: 'pointer', userSelect: 'none' }}>
                  Rate (req/min) {sortConfig.column === 'rate' && (
                    <i className={`bi bi-arrow-${sortConfig.direction === 'asc' ? 'up' : 'down'}`}></i>
                  )}
                </th>
                <th onClick={() => handleSort('error_rate')} style={{ width: "100px", cursor: 'pointer', userSelect: 'none' }}>
                  Error Rate {sortConfig.column === 'error_rate' && (
                    <i className={`bi bi-arrow-${sortConfig.direction === 'asc' ? 'up' : 'down'}`}></i>
                  )}
                </th>
                <th onClick={() => handleSort('p50')} style={{ width: "100px", cursor: 'pointer', userSelect: 'none' }}>
                  P50 {sortConfig.column === 'p50' && (
                    <i className={`bi bi-arrow-${sortConfig.direction === 'asc' ? 'up' : 'down'}`}></i>
                  )}
                </th>
                <th onClick={() => handleSort('p95')} style={{ width: "100px", cursor: 'pointer', userSelect: 'none' }}>
                  P95 {sortConfig.column === 'p95' && (
                    <i className={`bi bi-arrow-${sortConfig.direction === 'asc' ? 'up' : 'down'}`}></i>
                  )}
                </th>
                <th onClick={() => handleSort('p99')} style={{ width: "100px", cursor: 'pointer', userSelect: 'none' }}>
                  P99 {sortConfig.column === 'p99' && (
                    <i className={`bi bi-arrow-${sortConfig.direction === 'asc' ? 'up' : 'down'}`}></i>
                  )}
                </th>
                <th style={{ width: "200px" }}>Actions</th>
              </tr>
            </thead>
            <tbody>
              {sortedServices.map((service: Service, index: number) => (
                <tr key={`${service.name}-${service.namespace || "default"}-${index}`} style={{ cursor: "pointer" }}>
                  <td>
                    <strong>{service.name}</strong>
                  </td>
                  <td>
                    {service.namespace ? (
                      <Badge bg="light" text="dark">
                        {service.namespace}
                      </Badge>
                    ) : (
                      <span className="text-muted">-</span>
                    )}
                  </td>
                  <td>
                    {service.metrics?.request_count ? (
                      <span>{formatNumber(calculateRequestRate(service.metrics.request_count))} <span className="text-muted small">({formatNumber(service.metrics.request_count)})</span></span>
                    ) : (
                      <span className="text-muted">-</span>
                    )}
                  </td>
                  <td>
                    {service.metrics?.error_rate !== undefined
                      ? getErrorRateBadge(service.metrics.error_rate)
                      : <span className="text-muted">-</span>}
                  </td>
                  <td>
                    {service.metrics?.p50_latency_ms ? (
                      <span className="small">{formatDuration(service.metrics.p50_latency_ms / 1000)}</span>
                    ) : (
                      <span className="text-muted">-</span>
                    )}
                  </td>
                  <td>
                    {service.metrics?.p95_latency_ms ? (
                      <Badge bg={getLatencyColor(service.metrics.p95_latency_ms)} className="small">
                        {formatDuration(service.metrics.p95_latency_ms / 1000)}
                      </Badge>
                    ) : (
                      <span className="text-muted">-</span>
                    )}
                  </td>
                  <td>
                    {service.metrics?.p99_latency_ms ? (
                      <span className="small text-danger">{formatDuration(service.metrics.p99_latency_ms / 1000)}</span>
                    ) : (
                      <span className="text-muted">-</span>
                    )}
                  </td>
                  <td>
                    <ButtonGroup size="sm">
                      <Button
                        variant="outline-primary"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleViewSpans(service.name, service.namespace);
                        }}
                        title="View spans for this service"
                      >
                        <i className="bi bi-diagram-3"></i>
                      </Button>
                      <Button
                        variant="outline-secondary"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleViewLogs(service.name, service.namespace);
                        }}
                        title="View logs for this service"
                      >
                        <i className="bi bi-file-text"></i>
                      </Button>
                      <Button
                        variant="outline-info"
                        onClick={(e) => {
                          e.stopPropagation();
                          handleViewMetrics(service.name, service.namespace);
                        }}
                        title="View metrics for this service"
                      >
                        <i className="bi bi-graph-up"></i>
                      </Button>
                    </ButtonGroup>
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card.Body>
      </Card>

      <div className="mt-3 text-muted small">
        <p className="mb-1">
          <strong>RED Metrics:</strong> Rate (requests/sec) · Errors (error rate %) · Duration (latency percentiles)
        </p>
        <p className="mb-0">
          <i className="bi bi-info-circle me-1"></i>
          Services are automatically discovered from spans with <code>service.name</code> attributes.
        </p>
      </div>
    </div>
  );
}
