import { getWebAutoInstrumentations } from '@opentelemetry/auto-instrumentations-web';

/**
 * Get configured OpenTelemetry instrumentations for browser
 * Uses the auto-instrumentations-web meta-package for comprehensive coverage
 */
export function getInstrumentations() {
  return getWebAutoInstrumentations({
    // DocumentLoad instrumentation - captures page load performance
    '@opentelemetry/instrumentation-document-load': {
      enabled: true,
    },
    // UserInteraction instrumentation - tracks clicks, form submits, keypresses
    '@opentelemetry/instrumentation-user-interaction': {
      enabled: true,
      eventNames: ['click', 'submit', 'keypress'],
      // Don't track interactions on password fields
      shouldPreventSpanCreation: (_eventType, element) => {
        if (element.getAttribute('type') === 'password') {
          return true;
        }
        // Don't track hidden elements
        if (element.offsetParent === null) {
          return true;
        }
        return false;
      },
    },
    // Fetch instrumentation - automatically traces API calls
    '@opentelemetry/instrumentation-fetch': {
      enabled: true,
      // Propagate trace context to these origins
      propagateTraceHeaderCorsUrls: [
        /^https?:\/\/localhost/,
        /^https?:\/\/.*\.ollyscale\.test/,
        new RegExp(`^${window.location.origin}`),
      ],
      // Don't instrument health/ping endpoints or telemetry itself
      ignoreUrls: [
        /\/health$/,
        /\/ping$/,
        /\/v1\/traces$/,
        /\/v1\/metrics$/,
        /\/v1\/logs$/,
      ],
      clearTimingResources: true,
      applyCustomAttributesOnSpan: (span, _request, response) => {
        if (response instanceof Response) {
          span.setAttribute('http.response.content_length', response.headers.get('content-length') || 0);
          span.setAttribute('http.response.content_type', response.headers.get('content-type') || 'unknown');
        }
      },
    },
    // XML HTTP Request instrumentation
    '@opentelemetry/instrumentation-xml-http-request': {
      enabled: true,
      propagateTraceHeaderCorsUrls: [
        /^https?:\/\/localhost/,
        /^https?:\/\/.*\.ollyscale\.test/,
        new RegExp(`^${window.location.origin}`),
      ],
    },
  });
}
