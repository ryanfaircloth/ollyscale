import { Component, type ReactNode, type ErrorInfo } from 'react';
import { Alert, Button, Container } from 'react-bootstrap';
import { trace, SpanStatusCode } from '@opentelemetry/api';
import { hasTelemetryConsent } from '@/telemetry/config';

interface ErrorBoundaryProps {
  children: ReactNode;
  fallback?: (error: Error, errorInfo: ErrorInfo, resetError: () => void) => ReactNode;
}

interface ErrorBoundaryState {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
}

/**
 * ErrorBoundary component catches React errors and reports them to OpenTelemetry
 * Wraps the entire app to catch component errors that would otherwise crash the app
 */
export class ErrorBoundary extends Component<ErrorBoundaryProps, ErrorBoundaryState> {
  constructor(props: ErrorBoundaryProps) {
    super(props);
    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
    };
  }

  static getDerivedStateFromError(error: Error): Partial<ErrorBoundaryState> {
    // Update state so the next render shows fallback UI
    return {
      hasError: true,
      error,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo): void {
    // Log error to console
    console.error('[ErrorBoundary] Component error caught:', error, errorInfo);

    // Store errorInfo in state for display
    this.setState({ errorInfo });

    // Report to OpenTelemetry if consent given
    if (hasTelemetryConsent()) {
      try {
        // Get tracer - this should use the registered provider
        const tracer = trace.getTracer('ollyscale-web-ui');
        console.log('[ErrorBoundary] Got tracer:', tracer);

        const span = tracer.startSpan('error.react_boundary', {
          attributes: {
            'error.type': error.name,
            'error.message': error.message,
            'error.stack': error.stack || '',
            'react.component_stack': errorInfo.componentStack || '',
          },
        });

        console.log('[ErrorBoundary] Created span:', span);

        span.recordException({
          name: error.name,
          message: error.message,
          stack: error.stack,
        });

        span.setStatus({
          code: SpanStatusCode.ERROR,
          message: error.message,
        });

        span.end();

        console.log('[ErrorBoundary] Error reported to telemetry successfully');
      } catch (telemetryError) {
        console.error('[ErrorBoundary] Failed to report to telemetry:', telemetryError);
      }
    } else {
      console.log('[ErrorBoundary] Telemetry consent not given, skipping reporting');
    }
  }

  resetError = (): void => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
    });
  };

  render(): ReactNode {
    if (this.state.hasError) {
      // Custom fallback provided
      if (this.props.fallback) {
        return this.props.fallback(this.state.error!, this.state.errorInfo!, this.resetError);
      }

      // Default fallback UI
      return (
        <Container className="mt-5">
          <Alert variant="danger">
            <Alert.Heading>
              <i className="bi bi-exclamation-triangle me-2"></i>
              Something went wrong
            </Alert.Heading>
            <p>
              An unexpected error occurred in the application. This error has been logged and reported.
            </p>
            <hr />
            <div className="mb-3">
              <strong>Error:</strong>
              <pre className="mt-2 p-2 bg-light border rounded">
                <code>{this.state.error?.message}</code>
              </pre>
            </div>
            {import.meta.env.DEV && this.state.error?.stack && (
              <details className="mb-3">
                <summary className="text-muted" style={{ cursor: 'pointer' }}>
                  <small>Stack trace (development only)</small>
                </summary>
                <pre className="mt-2 p-2 bg-light border rounded" style={{ fontSize: '0.75rem' }}>
                  <code>{this.state.error.stack}</code>
                </pre>
              </details>
            )}
            {import.meta.env.DEV && this.state.errorInfo?.componentStack && (
              <details className="mb-3">
                <summary className="text-muted" style={{ cursor: 'pointer' }}>
                  <small>Component stack (development only)</small>
                </summary>
                <pre className="mt-2 p-2 bg-light border rounded" style={{ fontSize: '0.75rem' }}>
                  <code>{this.state.errorInfo.componentStack}</code>
                </pre>
              </details>
            )}
            <div className="d-flex gap-2">
              <Button variant="primary" onClick={this.resetError}>
                <i className="bi bi-arrow-clockwise me-2"></i>
                Try Again
              </Button>
              <Button variant="outline-secondary" onClick={() => window.location.reload()}>
                <i className="bi bi-arrow-repeat me-2"></i>
                Reload Page
              </Button>
              <Button
                variant="outline-secondary"
                onClick={() => {
                  window.location.href = '/';
                }}
              >
                <i className="bi bi-house me-2"></i>
                Go Home
              </Button>
            </div>
          </Alert>
        </Container>
      );
    }

    return this.props.children;
  }
}
