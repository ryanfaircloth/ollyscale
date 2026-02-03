import { Badge, Button } from 'react-bootstrap';
import { useQuery } from '@/contexts/QueryContext';

interface QuerySummaryProps {
  onExpand: () => void;
}

/**
 * Compact summary of active query filters shown when builder is collapsed
 * Shows badges for time range, live mode, filters, namespaces, services, and free text search
 */
export function QuerySummary({ onExpand }: QuerySummaryProps) {
  const { queryState } = useQuery();

  const activeFiltersCount =
    queryState.filters.length +
    (queryState.freeTextSearch ? 1 : 0) +
    queryState.selectedNamespaces.length +
    queryState.selectedServices.length;

  // Format time range for display
  const getTimeRangeLabel = () => {
    if (queryState.liveMode && queryState.relativeMinutes) {
      const hours = Math.floor(queryState.relativeMinutes / 60);
      const mins = queryState.relativeMinutes % 60;
      if (hours > 0) {
        return `Last ${hours}h ${mins > 0 ? mins + 'm' : ''}`;
      }
      return `Last ${mins}m`;
    }
    // Show abbreviated timestamps for historical mode
    const start = new Date(queryState.timeRange.start_time);
    const end = new Date(queryState.timeRange.end_time);
    return `${start.toLocaleString('en-US', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })} → ${end.toLocaleString('en-US', { hour: '2-digit', minute: '2-digit' })}`;
  };

  return (
    <div className="d-flex align-items-center gap-2 py-2">
      {/* Expand button */}
      <Button
        variant="outline-secondary"
        size="sm"
        onClick={onExpand}
        title="Edit query"
      >
        <i className="bi bi-funnel me-1"></i>
        Edit Query
      </Button>

      {/* Live mode indicator */}
      <Badge
        bg={queryState.liveMode ? 'success' : 'secondary'}
        className="d-flex align-items-center gap-1"
        style={{ fontSize: '0.75rem', fontWeight: 'normal' }}
      >
        <i className={`bi bi-${queryState.liveMode ? 'broadcast' : 'pause-circle'}`}></i>
        {queryState.liveMode ? 'LIVE' : 'PAUSED'}
      </Badge>

      {/* Time range */}
      <Badge bg="primary" style={{ fontSize: '0.75rem', fontWeight: 'normal' }}>
        <i className="bi bi-clock me-1"></i>
        {getTimeRangeLabel()}
      </Badge>

      {/* Time field */}
      <Badge bg="info" style={{ fontSize: '0.75rem', fontWeight: 'normal' }}>
        <i className="bi bi-calendar-event me-1"></i>
        {queryState.timeField === 'event_time' ? 'Event Time' : queryState.timeField === 'db_time' ? 'DB Time' : 'Observed Time'}
      </Badge>

      {/* Active filters count */}
      {activeFiltersCount > 0 && (
        <Badge bg="warning" text="dark" style={{ fontSize: '0.75rem', fontWeight: 'normal' }}>
          <i className="bi bi-filter me-1"></i>
          {activeFiltersCount} {activeFiltersCount === 1 ? 'filter' : 'filters'}
        </Badge>
      )}

      {/* Namespaces */}
      {queryState.selectedNamespaces.length > 0 && (
        <Badge bg="secondary" style={{ fontSize: '0.75rem', fontWeight: 'normal' }}>
          <i className="bi bi-box me-1"></i>
          {queryState.selectedNamespaces.length} namespace{queryState.selectedNamespaces.length > 1 ? 's' : ''}
        </Badge>
      )}

      {/* Services */}
      {queryState.selectedServices.length > 0 && (
        <Badge bg="secondary" style={{ fontSize: '0.75rem', fontWeight: 'normal' }}>
          <i className="bi bi-server me-1"></i>
          {queryState.selectedServices.length} service{queryState.selectedServices.length > 1 ? 's' : ''}
        </Badge>
      )}

      {/* Free text search */}
      {queryState.freeTextSearch && (
        <Badge bg="secondary" style={{ fontSize: '0.75rem', fontWeight: 'normal' }} title={queryState.freeTextSearch}>
          <i className="bi bi-search me-1"></i>
          "{queryState.freeTextSearch.substring(0, 20)}{queryState.freeTextSearch.length > 20 ? '...' : ''}"
        </Badge>
      )}
    </div>
  );
}
