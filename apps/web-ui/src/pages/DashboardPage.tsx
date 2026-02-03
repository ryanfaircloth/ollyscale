import { Row, Col, Card, Alert, Badge, Button } from 'react-bootstrap';
import { useTranslation } from 'react-i18next';
import { useHealthCheck } from '@/api/health';

export default function DashboardPage() {
  const { t } = useTranslation();
  const { data: health, isLoading, error, refetch } = useHealthCheck();

  return (
    <div>
      <div className="d-flex justify-content-end align-items-center mb-4">
        <Button variant="outline-secondary" size="sm" onClick={() => refetch()}>
          <i className="bi bi-arrow-clockwise me-1"></i>
          {t('common.refresh')}
        </Button>
      </div>

      {/* API Status Banner */}
      {isLoading && (
        <Alert variant="info" className="mb-4">
          <i className="bi bi-hourglass-split me-2"></i>
          {t('dashboard.checkingConnection', 'Checking API connection...')}
        </Alert>
      )}

      {error && (
        <Alert variant="danger" className="mb-4">
          <Alert.Heading>
            <i className="bi bi-exclamation-triangle-fill me-2"></i>
            {t('dashboard.connectionFailed', 'API Connection Failed')}
          </Alert.Heading>
          <p className="mb-2">
            {t('dashboard.cannotConnect', 'Cannot connect to the backend at')} <code>{import.meta.env.VITE_API_URL || window.location.origin}</code>
          </p>
          <p className="mb-0">
            <strong>{t('dashboard.troubleshooting', 'Troubleshooting')}:</strong>
          </p>
          <ul className="mb-0">
            <li>{t('dashboard.troubleshoot.backend', 'Make sure the ollyscale backend is running')}</li>
            <li>Docker: <code>cd docker && ./01-start-core.sh</code></li>
            <li>Kubernetes: <code>cd charts && ./install.sh</code></li>
            <li>{t('dashboard.troubleshoot.port', 'Check that port 5002 is accessible')}</li>
          </ul>
        </Alert>
      )}

      {health && (
        <Alert variant="success" className="mb-4">
          <div className="d-flex justify-content-between align-items-center">
            <div>
              <i className="bi bi-check-circle-fill me-2"></i>
              <strong>{t('dashboard.apiConnected', 'API Connected')}</strong>
              {health.version && (
                <Badge bg="light" text="dark" className="ms-2">
                  v{health.version}
                </Badge>
              )}
            </div>
            <div className="text-end">
              {health.redis_connected !== undefined && (
                <Badge bg={health.redis_connected ? 'success' : 'danger'} className="me-2">
                  Redis: {health.redis_connected ? t('dashboard.connected', 'Connected') : t('dashboard.disconnected', 'Disconnected')}
                </Badge>
              )}
              {health.uptime && <small className="text-muted">{t('dashboard.uptime', 'Uptime')}: {health.uptime}</small>}
            </div>
          </div>
        </Alert>
      )}

      <Row className="g-3">
        <Col md={3}>
          <Card>
            <Card.Body>
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h6 className="text-muted mb-1">{t('dashboard.stats.traces', 'Total Traces')}</h6>
                  <h3 className="mb-0">-</h3>
                </div>
                <i className="bi bi-diagram-3 text-primary" style={{ fontSize: '2rem' }}></i>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col md={3}>
          <Card>
            <Card.Body>
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h6 className="text-muted mb-1">{t('dashboard.stats.services', 'Active Services')}</h6>
                  <h3 className="mb-0">-</h3>
                </div>
                <i className="bi bi-server text-success" style={{ fontSize: '2rem' }}></i>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col md={3}>
          <Card>
            <Card.Body>
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h6 className="text-muted mb-1">{t('dashboard.errorRate', 'Error Rate')}</h6>
                  <h3 className="mb-0">-</h3>
                </div>
                <i className="bi bi-exclamation-triangle text-danger" style={{ fontSize: '2rem' }}></i>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col md={3}>
          <Card>
            <Card.Body>
              <div className="d-flex justify-content-between align-items-center">
                <div>
                  <h6 className="text-muted mb-1">{t('dashboard.avgLatency', 'Avg Latency')}</h6>
                  <h3 className="mb-0">-</h3>
                </div>
                <i className="bi bi-clock text-info" style={{ fontSize: '2rem' }}></i>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row className="mt-4">
        <Col>
          <Card>
            <Card.Header>
              <h5 className="mb-0">{t('dashboard.gettingStarted', 'Quick Start')}</h5>
            </Card.Header>
            <Card.Body>
              <p>{t('dashboard.welcome', 'Welcome to ollyScale! This observability platform helps you monitor and debug your applications.')}</p>
              <ul>
                <li><strong>{t('nav.traces', 'Traces')}</strong>: {t('dashboard.tracesDesc', 'View distributed traces across your services')}</li>
                <li><strong>{t('nav.logs', 'Logs')}</strong>: {t('dashboard.logsDesc', 'Search and correlate application logs')}</li>
                <li><strong>{t('nav.metrics', 'Metrics')}</strong>: {t('dashboard.metricsDesc', 'Monitor service performance metrics')}</li>
                <li><strong>{t('nav.map', 'Service Map')}</strong>: {t('dashboard.serviceMapDesc', 'Visualize service dependencies')}</li>
              </ul>
              <p className="mb-0">
                {t('dashboard.startBy', 'Start by sending OpenTelemetry data to')} <code>http://localhost:4343</code>
              </p>
            </Card.Body>
          </Card>
        </Col>
      </Row>
    </div>
  );
}
