import { WebTracerProvider, SimpleSpanProcessor } from '@opentelemetry/sdk-trace-web';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { SEMRESATTRS_SERVICE_NAME, SEMRESATTRS_SERVICE_VERSION } from '@opentelemetry/semantic-conventions';
import { resourceFromAttributes } from '@opentelemetry/resources';
import { registerInstrumentations } from '@opentelemetry/instrumentation';
import { trace, SpanStatusCode } from '@opentelemetry/api';
import { getInstrumentations } from './instrumentations';

// Get telemetry consent from localStorage
export function hasTelemetryConsent(): boolean {
  if (typeof window === 'undefined') return false;
  const consent = localStorage.getItem('ollyscale-telemetry-consent');
  return consent === 'true';
}

// Get OTLP endpoint from environment or default to current host
function getOTLPEndpoint(): string {
  // In production, use the same host (gateway will route to browser collector)
  // In development, use localhost:5002 which proxies to the API
  const isDevelopment = import.meta.env.DEV;
  if (isDevelopment) {
    return 'http://localhost:5002/v1/traces';
  }
  // Production: use current origin + /v1/traces (HTTPRoute routes to browser collector)
  return `${window.location.origin}/v1/traces`;
}

// Initialize OpenTelemetry
export function initializeTelemetry(): void {
  // Check consent first
  if (!hasTelemetryConsent()) {
    console.log('[Telemetry] User has not consented to telemetry. Skipping initialization.');
    return;
  }

  console.log('[Telemetry] Initializing OpenTelemetry browser instrumentation...');

  // Create OTLP exporter
  const otlpExporter = new OTLPTraceExporter({
    url: getOTLPEndpoint(),
    headers: {
      'Content-Type': 'application/json',
    },
  });

  // Create tracer provider with resource attributes and span processors
  const resource = resourceFromAttributes({
    [SEMRESATTRS_SERVICE_NAME]: 'ollyscale-web-ui',
    [SEMRESATTRS_SERVICE_VERSION]: import.meta.env.VITE_APP_VERSION || '0.0.0-dev',
    'deployment.environment': import.meta.env.MODE || 'development',
  });

  // Create simple span processor for immediate export (testing)
  const spanProcessor = new SimpleSpanProcessor(otlpExporter);

  // Create provider with span processor (as per official docs)
  const provider = new WebTracerProvider({
    resource,
    spanProcessors: [spanProcessor],
  });

  // Register the provider
  provider.register();

  // Register instrumentations
  registerInstrumentations({
    instrumentations: getInstrumentations(),
  });

  // Install global error handlers
  installGlobalErrorHandlers();

  console.log('[Telemetry] OpenTelemetry initialized successfully');
  console.log('[Telemetry] Exporting traces to:', getOTLPEndpoint());
}

/**
 * Install global error handlers to capture unhandled exceptions
 * These handlers create spans for errors that would otherwise go untracked
 */
function installGlobalErrorHandlers(): void {
  // Handle synchronous errors (window.onerror)
  window.addEventListener('error', (event: ErrorEvent) => {
    if (!hasTelemetryConsent()) return;

    // Get tracer from registered provider (not module-level no-op)
    const tracer = trace.getTracer('ollyscale-web-ui');
    const span = tracer.startSpan('error.unhandled', {
      attributes: {
        'error.type': event.error?.name || 'Error',
        'error.message': event.message,
        'error.filename': event.filename,
        'error.lineno': event.lineno,
        'error.colno': event.colno,
        'error.stack': event.error?.stack || '',
      },
    });

    span.recordException({
      name: event.error?.name || 'Error',
      message: event.message,
      stack: event.error?.stack,
    });

    span.setStatus({
      code: SpanStatusCode.ERROR,
      message: event.message,
    });

    span.end();

    console.error('[Telemetry] Unhandled error captured:', event.message);
  });

  // Handle unhandled promise rejections (window.onunhandledrejection)
  window.addEventListener('unhandledrejection', (event: PromiseRejectionEvent) => {
    if (!hasTelemetryConsent()) return;

    // Get tracer from registered provider (not module-level no-op)
    const tracer = trace.getTracer('ollyscale-web-ui');
    const reason = event.reason;
    const errorMessage = reason instanceof Error ? reason.message : String(reason);
    const errorStack = reason instanceof Error ? reason.stack : undefined;

    const span = tracer.startSpan('error.unhandled_rejection', {
      attributes: {
        'error.type': reason instanceof Error ? reason.name : 'UnhandledRejection',
        'error.message': errorMessage,
        'error.stack': errorStack || '',
      },
    });

    span.recordException({
      name: reason instanceof Error ? reason.name : 'UnhandledRejection',
      message: errorMessage,
      stack: errorStack,
    });

    span.setStatus({
      code: SpanStatusCode.ERROR,
      message: errorMessage,
    });

    span.end();

    console.error('[Telemetry] Unhandled promise rejection captured:', errorMessage);
  });

  console.log('[Telemetry] Global error handlers installed');
}

// Shutdown telemetry (call on app unmount if needed)
export async function shutdownTelemetry(): Promise<void> {
  console.log('[Telemetry] Shutting down...');
  // Provider shutdown would go here if we kept a reference
}
