import { useState } from "react";
import { Card, Button, ButtonGroup, Badge, Alert } from "react-bootstrap";
import { useTranslation } from 'react-i18next';
import { useServiceMapQuery } from "@/api/queries/useServicesQuery";
import { useAutoRefresh } from "@/hooks/useAutoRefresh";
import { LoadingSpinner } from "@/components/common/LoadingSpinner";
import { EmptyState } from "@/components/common/EmptyState";
import { ServiceGraph } from "@/components/servicemap/ServiceGraph";

export default function ServiceMapPage() {
  const { t } = useTranslation();
  const [layout, setLayout] = useState<"hierarchical" | "grid">("hierarchical");

  // Time range: last 30 minutes (updates on re-render)
  const getTimeRange = () => {
    const now = new Date();
    const thirtyMinutesAgo = new Date(now.getTime() - 30 * 60 * 1000);
    return {
      start_time: thirtyMinutesAgo.toISOString(),
      end_time: now.toISOString(),
    };
  };
  const [timeRange, setTimeRange] = useState(getTimeRange);

  const { data, isLoading, error, refetch } = useServiceMapQuery(timeRange);

  // Wrap refetch to also update time range
  const refreshData = () => {
    setTimeRange(getTimeRange());
    refetch();
  };

  // Auto-refresh
  useAutoRefresh(() => refreshData());

  if (isLoading) {
    return <LoadingSpinner message={t('serviceMap.loading', 'Loading service map...')} />;
  }

  if (error) {
    return (
      <Alert variant="danger" className="m-3">
        <Alert.Heading>{t('serviceMap.errorLoading', 'Error loading service map')}</Alert.Heading>
        <p>{error instanceof Error ? error.message : t('errors.unknown', 'Unknown error')}</p>
      </Alert>
    );
  }

  if (!data || !data.nodes) {
    return <LoadingSpinner message={t('serviceMap.loading', 'Loading service map...')} />;
  }

  const totalNodes = data.nodes.length;

  if (totalNodes === 0) {
    return (
      <EmptyState
        title={t('serviceMap.noData', 'No service map data')}
        description={t('serviceMap.noDataDesc', 'No service dependencies detected yet. The service map is automatically built from trace data showing service-to-service calls.')}
      />
    );
  }

  return (
    <div>
      <Card className="mb-3">
        <Card.Body className="py-2">
          <div className="d-flex justify-content-between align-items-center flex-wrap gap-2">
            <div className="d-flex flex-wrap gap-3 align-items-center">
              <div>
                <strong>{t('serviceMap.legend', 'Legend')}:</strong>
              </div>
              <div>
                <Badge bg="primary" className="me-2" title="Rectangle - Blue">
                  <i className="bi bi-square-fill me-1"></i>{t('serviceMap.nodeTypes.client', 'Client')}
                </Badge>
                <Badge bg="success" className="me-2" title="Ellipse - Green">
                  <i className="bi bi-circle-fill me-1"></i>{t('serviceMap.nodeTypes.server', 'Server')}
                </Badge>
                <Badge bg="info" className="me-2" title="Hexagon - Cyan">
                  <i className="bi bi-hexagon-fill me-1"></i>{t('serviceMap.nodeTypes.database', 'Database')}
                </Badge>
                <Badge bg="warning" text="dark" className="me-2" title="Octagon - Yellow">
                  <i className="bi bi-octagon-fill me-1"></i>Messaging
                </Badge>
                <Badge bg="danger" className="me-2" title="Triangle - Red">
                  <i className="bi bi-triangle-fill me-1"></i>External
                </Badge>
                <Badge bg="secondary" title="Diamond - Gray dashed">
                  <i className="bi bi-diamond-fill me-1"></i>Isolated
                </Badge>
              </div>
            </div>
            <div className="d-flex gap-2 align-items-center">
              <ButtonGroup size="sm">
                <Button
                  variant={layout === "hierarchical" ? "primary" : "outline-primary"}
                  onClick={() => setLayout("hierarchical")}
                >
                  <i className="bi bi-diagram-3 me-1"></i>
                  Hierarchical
                </Button>
                <Button
                  variant={layout === "grid" ? "primary" : "outline-primary"}
                  onClick={() => setLayout("grid")}
                >
                  <i className="bi bi-grid-3x3 me-1"></i>
                  Grid
                </Button>
              </ButtonGroup>
            </div>
          </div>
        </Card.Body>
      </Card>
      <Card>
        <Card.Body style={{ height: "650px", position: "relative", padding: 0 }}>
          <ServiceGraph nodes={data.nodes} edges={data.edges || []} layout={layout} />
        </Card.Body>
      </Card>
    </div>
  );
}
