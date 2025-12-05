/**
 * Filter Module - Manages hiding TinyOlly's own telemetry
 */

let hideTinyOlly = false;

// Load state from localStorage
try {
    hideTinyOlly = localStorage.getItem('tinyolly-hide-self') === 'true';
} catch (e) {
    console.warn('LocalStorage access failed:', e);
}

export function initHideTinyOllyToggle() {
    updateHideTinyOllyButton();
}

export function toggleHideTinyOlly() {
    hideTinyOlly = !hideTinyOlly;
    try {
        localStorage.setItem('tinyolly-hide-self', hideTinyOlly);
    } catch (e) {
        console.warn('LocalStorage access failed:', e);
    }
    updateHideTinyOllyButton();

    // Reload current tab data
    import('./tabs.js').then(module => {
        const currentTab = module.getCurrentTab ? module.getCurrentTab() : 'logs';
        if (currentTab === 'logs') {
            import('./api.js').then(api => api.loadLogs());
        } else if (currentTab === 'spans') {
            import('./spans.js').then(spansModule => {
                const serviceFilter = spansModule.getServiceFilter ? spansModule.getServiceFilter() : null;
                import('./api.js').then(api => api.loadSpans(serviceFilter));
            });
        } else if (currentTab === 'traces') {
            import('./api.js').then(api => api.loadTraces());
        } else if (currentTab === 'metrics') {
            import('./api.js').then(api => api.loadMetrics());
        } else if (currentTab === 'catalog') {
            import('./api.js').then(api => api.loadServiceCatalog());
        } else if (currentTab === 'map') {
            import('./api.js').then(api => api.loadServiceMap());
        }
    });
}

function updateHideTinyOllyButton() {
    const btn = document.getElementById('hide-tinyolly-btn');
    const text = document.getElementById('hide-tinyolly-text');

    if (!btn || !text) return;

    if (hideTinyOlly) {
        text.textContent = 'Show TinyOlly';
        btn.title = 'TinyOlly telemetry is hidden - click to show';
    } else {
        text.textContent = 'Hide TinyOlly';
        btn.title = 'TinyOlly telemetry is visible - click to hide';
    }
}

/**
 * Check if TinyOlly telemetry should be hidden
 */
export function shouldHideTinyOlly() {
    return hideTinyOlly;
}

/**
 * Filter function to exclude tinyolly-ui service
 */
export function filterTinyOllyData(item) {
    if (!hideTinyOlly) return true;

    // Check various service name fields
    const serviceName = item.service_name ||
                       item.serviceName ||
                       item.service ||
                       item.name ||
                       (item.attributes && (
                           item.attributes['service.name'] ||
                           item.attributes.service_name
                       )) ||
                       (item.resource && item.resource['service.name']);

    // Filter out tinyolly-ui
    return serviceName !== 'tinyolly-ui';
}

/**
 * Filter traces - exclude if root service is tinyolly-ui
 */
export function filterTinyOllyTrace(trace) {
    if (!hideTinyOlly) return true;

    const rootService = trace.root_service || trace.rootService;
    return rootService !== 'tinyolly-ui';
}

/**
 * Filter metrics - exclude if service.name is tinyolly-ui
 */
export function filterTinyOllyMetric(metric) {
    if (!hideTinyOlly) return true;

    // Check in resources array
    if (metric.resources) {
        const serviceName = metric.resources['service.name'];
        if (serviceName === 'tinyolly-ui') return false;
    }

    // Check in series
    if (metric.series && Array.isArray(metric.series)) {
        // Filter out entire metric if all series are from tinyolly-ui
        const nonTinyOllySeries = metric.series.filter(s => {
            const serviceName = s.resources && s.resources['service.name'];
            return serviceName !== 'tinyolly-ui';
        });
        return nonTinyOllySeries.length > 0;
    }

    return true;
}

/**
 * Filter metric series - exclude series from tinyolly-ui
 */
export function filterTinyOllyMetricSeries(series) {
    if (!hideTinyOlly) return series;

    return series.filter(s => {
        const serviceName = s.resources && s.resources['service.name'];
        return serviceName !== 'tinyolly-ui';
    });
}
