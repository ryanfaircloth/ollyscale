import { useState, useMemo, useEffect } from 'react';
import { useLocation } from 'react-router-dom';
import { Card, Table, Badge, Alert, Button, ButtonGroup, Collapse } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { useMetricsQuery } from '@/api/queries/useMetricsQuery';
import { useAutoRefresh } from '@/hooks/useAutoRefresh';
import { useQuery } from '@/contexts/QueryContext';
import { formatTimestamp, formatNumber } from '@/utils/formatting';
import { LoadingSpinner } from '@/components/common/LoadingSpinner';
import { EmptyState } from '@/components/common/EmptyState';
import { CompactQueryBuilder } from '@/components/query/CompactQueryBuilder';
import { METRIC_FIELD_SCHEMA } from '@/components/query/fieldSchemas';
import { MetricDetail } from '@/components/metric/MetricDetail';
import type { Metric } from '@/api/types/metric';
import type { Filter } from '@/api/types/common';

export default function MetricsPage() {
  const { t } = useTranslation();
  const location = useLocation();
  const { queryState, refreshTimeWindow, updateFilters } = useQuery();
  const [selectedMetric, setSelectedMetric] = useState<Metric | null>(null);
  const [showREDOnly, setShowREDOnly] = useState(false);
  const [showCardinalityExplorer, setShowCardinalityExplorer] = useState(false);

  // Apply initial filters from navigation state (e.g., from Service Catalog)
  useEffect(() => {
    const state = location.state as { initialFilters?: Filter[] } | null;
    if (state?.initialFilters) {
      updateFilters(state.initialFilters);
      // Clear the state to prevent reapplying filters on subsequent renders
      window.history.replaceState({}, document.title);
    }
  }, [location.state]);

  const { data, isLoading, error, refetch } = useMetricsQuery({
    time_range: queryState.timeRange,
    filters: queryState.filters,
    pagination: { limit: 1000 },
  });

  // Auto-refresh with time window sliding
  useAutoRefresh(() => {
    refreshTimeWindow();
    refetch();
  });

  const getMetricTypeBadge = (type: string) => {
    const typeMap: Record<string, string> = {
      Gauge: "primary",
      Sum: "success",
      Counter: "success",  // Legacy, maps to Sum
      Histogram: "info",
      ExponentialHistogram: "info",
      Summary: "warning",
    };
    const variant = typeMap[type] || "secondary";
    return <Badge bg={variant}>{type}</Badge>;
  };

  const formatValue = (dataPoints: any[]) => {
    if (!dataPoints || dataPoints.length === 0) return "-";
    const latest = dataPoints[dataPoints.length - 1];
    if (latest.value !== undefined) return formatNumber(latest.value);
    if (latest.sum !== undefined) return formatNumber(latest.sum);
    return '-';
  };

  // Filter for RED metrics (Rate, Error, Duration)
  const isREDMetric = (metricName: string): boolean => {
    const redPatterns = [
      /request.*rate|rate.*request/i,
      /request.*count|count.*request/i,
      /request.*total|total.*request/i,
      /error.*rate|rate.*error/i,
      /error.*count|count.*error/i,
      /error.*total|total.*error/i,
      /duration/i,
      /latency/i,
      /response.*time|time.*response/i,
      /_seconds_bucket/i,
      /_seconds_sum/i,
      /_seconds_count/i,
    ];
    return redPatterns.some(pattern => pattern.test(metricName));
  };

  // Compute cardinality from attributes
  const cardinalityAnalysis = useMemo(() => {
    if (!data?.metrics) return [];

    const analysis = data.metrics.map(metric => {
      // Collect unique attribute keys from all data points
      const labelKeysSet = new Set<string>();
      metric.data_points.forEach(dp => {
        if (dp.attributes) {
          Object.keys(dp.attributes).forEach(key => labelKeysSet.add(key));
        }
      });
      const labelKeys = Array.from(labelKeysSet);
      const seriesCount = metric.data_points.length;

      return {
        metric_name: metric.name,
        series_count: seriesCount,
        label_count: labelKeys.length,
        labels: labelKeys,
        is_high_cardinality: seriesCount > 100 || labelKeys.length > 5,
      };
    });

    return analysis.sort((a, b) => b.series_count - a.series_count);
  }, [data?.metrics]);

  // Filter metrics based on RED toggle
  const filteredMetrics = useMemo(() => {
    if (!data?.metrics) return [];
    if (!showREDOnly) return data.metrics;
    return data.metrics.filter(m => isREDMetric(m.name));
  }, [data?.metrics, showREDOnly]);

  const highCardinalityCount = cardinalityAnalysis.filter(m => m.is_high_cardinality).length;

  return (
    <>
      {/* Compact Query Builder */}
      <CompactQueryBuilder fieldSchema={METRIC_FIELD_SCHEMA} showFreeTextSearch={false} />

      {/* Filters and Tools */}
      {!isLoading && !error && data && data.metrics && data.metrics.length > 0 && (
        <div className="mb-3 d-flex gap-2 align-items-center">
          <ButtonGroup>
            <Button
              variant={showREDOnly ? 'primary' : 'outline-primary'}
              size="sm"
              onClick={() => setShowREDOnly(!showREDOnly)}
            >
              <i className="bi bi-funnel me-1"></i>
              {t('metrics.redOnly', 'RED Metrics Only')}
            </Button>
            <Button
              variant={showCardinalityExplorer ? 'warning' : 'outline-warning'}
              size="sm"
              onClick={() => setShowCardinalityExplorer(!showCardinalityExplorer)}
            >
              <i className="bi bi-bar-chart me-1"></i>
              Cardinality ({highCardinalityCount} high)
            </Button>
          </ButtonGroup>
          {showREDOnly && (
            <Badge bg="primary">
              Showing {filteredMetrics.length} of {data.metrics.length} metrics
            </Badge>
          )}
        </div>
      )}

      {/* Cardinality Explorer */}
      <Collapse in={showCardinalityExplorer}>
        <div>
          <Card className="mb-3 border-warning">
            <Card.Header className="bg-warning bg-opacity-10">
              <strong>
                <i className="bi bi-exclamation-triangle-fill text-warning me-2"></i>
                {t('metrics.cardinalityAnalysis', 'Cardinality Analysis')}
              </strong>
            </Card.Header>
            <Card.Body>
              <p className="small text-muted mb-3">
                {t('metrics.cardinalityDesc', 'High cardinality metrics (many unique label combinations or data points) can impact performance and storage. Consider reducing label dimensions or sampling rates.')}
              </p>
              <div style={{ maxHeight: '400px', overflow: 'auto' }}>
                <Table striped hover size="sm" className="mb-0">
                  <thead>
                    <tr>
                      <th>{t('metrics.name', 'Metric Name')}</th>
                      <th style={{ width: '120px' }}>{t('metrics.seriesCount', 'Series Count')}</th>
                      <th style={{ width: '120px' }}>{t('metrics.labelCount', 'Label Count')}</th>
                      <th>{t('metrics.labels', 'Labels')}</th>
                      <th style={{ width: '100px' }}>{t('common.status', 'Status')}</th>
                    </tr>
                  </thead>
                  <tbody>
                    {cardinalityAnalysis.map((analysis) => (
                      <tr key={analysis.metric_name}>
                        <td>
                          <code className="small">{analysis.metric_name}</code>
                        </td>
                        <td>
                          <Badge bg={analysis.series_count > 100 ? 'danger' : analysis.series_count > 50 ? 'warning' : 'success'}>
                            {analysis.series_count}
                          </Badge>
                        </td>
                        <td>
                          <Badge bg={analysis.label_count > 5 ? 'warning' : 'info'}>
                            {analysis.label_count}
                          </Badge>
                        </td>
                        <td>
                          <div className="small text-muted">
                            {analysis.labels.length > 0 ? analysis.labels.join(', ') : 'No labels'}
                          </div>
                        </td>
                        <td>
                          {analysis.is_high_cardinality ? (
                            <Badge bg="danger">High</Badge>
                          ) : (
                            <Badge bg="success">OK</Badge>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </Table>
              </div>
            </Card.Body>
          </Card>
        </div>
      </Collapse>

      {isLoading && <LoadingSpinner message="Loading metrics..." />}

      {error && (
        <Alert variant="danger">
          <Alert.Heading>Error loading metrics</Alert.Heading>
          <p>{error instanceof Error ? error.message : 'Unknown error'}</p>
        </Alert>
      )}

      {!isLoading && !error && (!data || !data.metrics || data.metrics.length === 0) && (
        <EmptyState
          title="No metrics found"
          description="No metrics match your current filters. Try adjusting your search criteria or wait for new metrics to arrive."
        />
      )}

      {!isLoading && !error && filteredMetrics.length === 0 && data && data.metrics.length > 0 && (
        <EmptyState
          title="No RED metrics found"
          description="No metrics match the RED pattern (Rate, Error, Duration). Toggle off the RED filter to see all metrics."
        />
      )}

      {!isLoading && !error && data && data.metrics && filteredMetrics.length > 0 && (
        <Card>
          <Card.Header>
            <strong>{filteredMetrics.length} metrics</strong>
            {showREDOnly && <Badge bg="primary" className="ms-2">RED filtered</Badge>}
          </Card.Header>
          <Card.Body className="p-0">
            <Table hover responsive className="mb-0">
            <thead>
              <tr>
                <th>Metric Name</th>
                <th style={{ width: "120px" }}>Type</th>
                <th style={{ width: "150px" }}>Latest Value</th>
                <th style={{ width: "120px" }}>Data Points</th>
                <th style={{ width: "140px" }}>Last Updated</th>
              </tr>
            </thead>
            <tbody>
              {filteredMetrics.map((metric: Metric, index: number) => (
                <tr
                  key={`${metric.name}-${index}`}
                  style={{ cursor: 'pointer' }}
                  onClick={() => setSelectedMetric(metric)}
                >
                  <td>
                    <strong>{metric.name}</strong>
                    {metric.description && (
                      <div className="small text-muted">{metric.description}</div>
                    )}
                  </td>
                  <td>{getMetricTypeBadge(metric.type)}</td>
                  <td className="text-end">
                    <code>{formatValue(metric.data_points)}</code>
                  </td>
                  <td className="text-center">
                    <Badge bg="info">{metric.data_points?.length || 0}</Badge>
                  </td>
                  <td className="small">
                    {metric.data_points && metric.data_points.length > 0
                      ? formatTimestamp(
                          metric.data_points[metric.data_points.length - 1].time
                            ? new Date(metric.data_points[metric.data_points.length - 1].time! / 1_000_000).toISOString()
                            : new Date().toISOString()
                        )
                      : '-'}
                  </td>
                </tr>
              ))}
            </tbody>
          </Table>
        </Card.Body>
      </Card>
      )}

      {/* Metric Detail Modal */}
      {selectedMetric && <MetricDetail metric={selectedMetric} onHide={() => setSelectedMetric(null)} />}
    </>
  );
}
