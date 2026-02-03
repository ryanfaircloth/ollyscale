import { useCallback } from 'react';
import { trace, SpanStatusCode, type Span } from '@opentelemetry/api';
import { hasTelemetryConsent } from '@/telemetry/config';

/**
 * Hook for creating custom spans in React components
 *
 * Usage:
 * ```tsx
 * const { startSpan, recordError } = useTracing();
 *
 * const handleClick = async () => {
 *   const span = startSpan('button.click', { 'button.id': 'save' });
 *   try {
 *     await saveData();
 *     span.setStatus({ code: SpanStatusCode.OK });
 *   } catch (error) {
 *     recordError(span, error);
 *   } finally {
 *     span.end();
 *   }
 * };
 * ```
 */
export function useTracing() {
  const startSpan = useCallback((
    name: string,
    attributes?: Record<string, string | number | boolean>
  ): Span => {
    // Return a no-op span if telemetry is not enabled
    if (!hasTelemetryConsent()) {
      console.log('[Telemetry] startSpan called but no consent:', name);
      return trace.getTracer('noop').startSpan(name);
    }

    // Get tracer from registered provider (not module-level no-op)
    const tracer = trace.getTracer('ollyscale-web-ui');
    const span = tracer.startSpan(name);
    console.log('[Telemetry] Created span:', name, 'with attributes:', attributes);

    if (attributes) {
      Object.entries(attributes).forEach(([key, value]) => {
        span.setAttribute(key, value);
      });
    }

    return span;
  }, []);

  const recordError = useCallback((span: Span, error: unknown): void => {
    if (!hasTelemetryConsent()) return;

    const errorMessage = error instanceof Error ? error.message : String(error);
    const errorStack = error instanceof Error ? error.stack : undefined;

    span.recordException({
      name: error instanceof Error ? error.name : 'Error',
      message: errorMessage,
      stack: errorStack,
    });

    span.setStatus({
      code: SpanStatusCode.ERROR,
      message: errorMessage,
    });
  }, []);

  const addEvent = useCallback((span: Span, name: string, attributes?: Record<string, string | number | boolean>): void => {
    if (!hasTelemetryConsent()) return;
    span.addEvent(name, attributes);
  }, []);

  /**
   * Track a business event (e.g., button click, filter applied, trace viewed)
   * Creates a span with short duration to represent the event
   */
  const trackEvent = useCallback((eventName: string, attributes?: Record<string, string | number | boolean>): void => {
    if (!hasTelemetryConsent()) return;

    const tracer = trace.getTracer('ollyscale-web-ui');
    const span = tracer.startSpan(eventName, {
      attributes: {
        'event.type': 'user_action',
        ...attributes,
      },
    });

    span.setStatus({ code: SpanStatusCode.OK });
    span.end();
  }, []);

  /**
   * Track a page view event
   */
  const trackPageView = useCallback((pageName: string, additionalAttributes?: Record<string, string | number | boolean>): void => {
    if (!hasTelemetryConsent()) return;

    const tracer = trace.getTracer('ollyscale-web-ui');
    const span = tracer.startSpan('page.view', {
      attributes: {
        'page.name': pageName,
        'page.url': window.location.pathname,
        'page.referrer': document.referrer,
        ...additionalAttributes,
      },
    });

    span.setStatus({ code: SpanStatusCode.OK });
    span.end();
  }, []);

  /**
   * Track a filter change event
   */
  const trackFilterChange = useCallback((filterType: string, filterValue: unknown): void => {
    if (!hasTelemetryConsent()) return;

    const tracer = trace.getTracer('ollyscale-web-ui');
    const span = tracer.startSpan('filter.changed', {
      attributes: {
        'filter.type': filterType,
        'filter.value': String(filterValue),
      },
    });

    span.setStatus({ code: SpanStatusCode.OK });
    span.end();
  }, []);

  /**
   * Track a data export event
   */
  const trackExport = useCallback((exportType: string, recordCount: number): void => {
    if (!hasTelemetryConsent()) return;

    const tracer = trace.getTracer('ollyscale-web-ui');
    const span = tracer.startSpan('data.export', {
      attributes: {
        'export.type': exportType,
        'export.record_count': recordCount,
      },
    });

    span.setStatus({ code: SpanStatusCode.OK });
    span.end();
  }, []);

  /**
   * Track a search query
   */
  const trackSearch = useCallback((searchType: string, queryLength: number, resultCount?: number): void => {
    if (!hasTelemetryConsent()) return;

    const tracer = trace.getTracer('ollyscale-web-ui');
    const span = tracer.startSpan('search.executed', {
      attributes: {
        'search.type': searchType,
        'search.query_length': queryLength,
        ...(resultCount !== undefined && { 'search.result_count': resultCount }),
      },
    });

    span.setStatus({ code: SpanStatusCode.OK });
    span.end();
  }, []);

  return {
    startSpan,
    recordError,
    addEvent,
    trackEvent,
    trackPageView,
    trackFilterChange,
    trackExport,
    trackSearch,
    forceFlush,
  };
}

/**
 * Utility to wrap async functions with automatic span creation
 *
 * Usage:
 * ```tsx
 * const tracedFetch = traceAsyncFunction('api.fetch', async () => {
 *   return await fetch('/api/data');
 * });
 * ```
 */
export function traceAsyncFunction<T>(
  name: string,
  fn: () => Promise<T>,
  attributes?: Record<string, string | number | boolean>
): Promise<T> {
  if (!hasTelemetryConsent()) {
    return fn();
  }

  const tracer = trace.getTracer('ollyscale-web-ui');
  const span = tracer.startSpan(name);

  if (attributes) {
    Object.entries(attributes).forEach(([key, value]) => {
      span.setAttribute(key, value);
    });
  }

  return fn()
    .then((result) => {
      span.setStatus({ code: SpanStatusCode.OK });
      return result;
    })
    .catch((error) => {
      const errorMessage = error instanceof Error ? error.message : String(error);
      span.recordException(error);
      span.setStatus({
        code: SpanStatusCode.ERROR,
        message: errorMessage,
      });
      throw error;
    })
    .finally(() => {
      span.end();
    });
}

/**
 * Force immediate export of all pending spans
 * Useful for testing to ensure spans are sent before assertions
 */
export async function forceFlush(): Promise<void> {
  if (!hasTelemetryConsent()) return;
  const provider = trace.getTracerProvider() as any;
  if (provider && typeof provider.forceFlush === 'function') {
    await provider.forceFlush();
  }
}
