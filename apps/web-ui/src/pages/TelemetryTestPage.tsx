import { useState, type ReactElement } from 'react';
import { Container, Row, Col, Card, Button, Alert } from 'react-bootstrap';
import { useTracing } from '@/hooks/useTracing';

/**
 * Telemetry Test Page - NOT IN NAVIGATION
 *
 * Access at: /telemetry-test
 *
 * This page is for testing browser telemetry error capture:
 * - Unhandled exceptions (window.onerror)
 * - Promise rejections (window.onunhandledrejection)
 * - React component errors (ErrorBoundary)
 */
// Component that throws during render (for ErrorBoundary testing)
function BrokenComponent(): ReactElement {
  throw new Error('Test React component error');
}

export function TelemetryTestPage() {
  const { startSpan, recordError, forceFlush } = useTracing();
  const [lastAction, setLastAction] = useState<string>('');
  const [shouldThrowReactError, setShouldThrowReactError] = useState(false);

  const throwSyncError = () => {
    setLastAction('Throwing synchronous error...');
    // This will be caught by window.onerror
    throw new Error('Test synchronous error from button click');
  };

  const throwAsyncError = () => {
    setLastAction('Throwing async error...');
    // This will be caught by window.onunhandledrejection
    Promise.reject(new Error('Test async promise rejection'));
  };

  const throwReactError = () => {
    setLastAction('Triggering React component error...');
    // Set state to render BrokenComponent, which will throw during render
    // This will be caught by ErrorBoundary
    setShouldThrowReactError(true);
  };

  const recordManualError = () => {
    setLastAction('Recording manual error...');
    const span = startSpan('user.action.manual_error_test');
    recordError(span, new Error('Test manually recorded error'));
    span.end();
  };

  const triggerSlowOperation = () => {
    setLastAction('Simulating slow operation...');
    const span = startSpan('user.action.slow_operation');
    span.setAttribute('test.type', 'performance');
    span.setAttribute('sampling.priority', 1); // Force sampling

    setTimeout(async () => {
      span.end();
      // Force immediate export for testing
      await forceFlush();
      setLastAction('Slow operation completed (check for span)');
    }, 2000);
  };

  const triggerCustomEvent = async () => {
    setLastAction('Recording custom event...');
    const span = startSpan('user.action.custom_event', {
      'event.type': 'test',
      'event.category': 'telemetry_verification',
      'event.value': 'custom_event_triggered',
      'sampling.priority': 1, // Force sampling
    });
    span.end();
    // Force immediate export for testing
    await forceFlush();
    setLastAction('Custom event recorded (check for span)');
  };

  return (
    <Container className="py-4">
      <Row>
        <Col>
          <h1 className="mb-4">Browser Telemetry Test Page</h1>

          <Alert variant="info">
            <Alert.Heading>How to Use This Page</Alert.Heading>
            <ol className="mb-0">
              <li>Click the test buttons below to trigger different error types</li>
              <li>Check browser console for error messages and telemetry logs</li>
              <li>Query the backend for spans: <code>service_name = 'ollyscale-web-ui'</code></li>
              <li>Look for span names: <code>error.unhandled</code>, <code>error.unhandled_rejection</code>, <code>error.react_boundary</code></li>
            </ol>
          </Alert>

          {lastAction && (
            <Alert variant="warning" dismissible onClose={() => setLastAction('')}>
              <strong>Last Action:</strong> {lastAction}
            </Alert>
          )}
        </Col>
      </Row>

      <Row className="g-3">
        <Col md={6}>
          <Card>
            <Card.Header className="bg-danger text-white">
              <strong>Error Tests</strong>
            </Card.Header>
            <Card.Body>
              <div className="d-grid gap-2">
                <Button variant="danger" onClick={throwSyncError}>
                  Throw Synchronous Error
                  <div className="small text-muted">Caught by window.onerror</div>
                </Button>

                <Button variant="danger" onClick={throwAsyncError}>
                  Throw Async Promise Rejection
                  <div className="small text-muted">Caught by window.onunhandledrejection</div>
                </Button>

                <Button variant="danger" onClick={throwReactError}>
                  Throw React Component Error
                  <div className="small text-muted">Caught by ErrorBoundary</div>
                </Button>
              </div>
            </Card.Body>
          </Card>
        </Col>

        <Col md={6}>
          <Card>
            <Card.Header className="bg-primary text-white">
              <strong>Span Tests</strong>
            </Card.Header>
            <Card.Body>
              <div className="d-grid gap-2">
                <Button variant="warning" onClick={recordManualError}>
                  Record Manual Error
                  <div className="small text-muted">Uses recordError() API</div>
                </Button>

                <Button variant="info" onClick={triggerSlowOperation}>
                  Trigger Slow Operation (2s)
                  <div className="small text-muted">Creates performance span</div>
                </Button>

                <Button variant="success" onClick={triggerCustomEvent}>
                  Trigger Custom Event
                  <div className="small text-muted">Creates custom span with attributes</div>
                </Button>
              </div>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      <Row className="mt-4">
        <Col>
          <Card>
            <Card.Header>
              <strong>Verification Commands</strong>
            </Card.Header>
            <Card.Body>
              <h6>API Query (curl):</h6>
              <pre className="bg-light p-2 rounded">
{`curl -X POST "https://ollyscale.ollyscale.test:49443/api/spans/search" \\
  -H "Content-Type: application/json" \\
  -d '{
    "time_range": {
      "start": "$(date -u -v-5M +%Y-%m-%dT%H:%M:%SZ)",
      "end": "$(date -u +%Y-%m-%dT%H:%M:%SZ)"
    },
    "filters": {
      "service_name": "ollyscale-web-ui"
    }
  }'`}
              </pre>

              <h6 className="mt-3">PostgreSQL Query:</h6>
              <pre className="bg-light p-2 rounded">
{`kubectl exec -n ollyscale deployment/ollyscale-db -c postgres -- \\
  psql -U ollyscale -d ollyscale -c \\
  "SELECT span_name, COUNT(*) FROM spans \\
   WHERE service_name = 'ollyscale-web-ui' \\
   GROUP BY span_name;"`}
              </pre>
            </Card.Body>
          </Card>
        </Col>
      </Row>

      {/* Conditionally render BrokenComponent to trigger ErrorBoundary */}
      {shouldThrowReactError && <BrokenComponent />}
    </Container>
  );
}
