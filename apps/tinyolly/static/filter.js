/*
 * BSD 3-Clause License
 *
 * Copyright (c) 2025, Infrastructure Architects, LLC
 * All rights reserved.
 *
 * Redistribution and use in source and binary forms, with or without
 * modification, are permitted provided that the following conditions are met:
 *
 * 1. Redistributions of source code must retain the above copyright notice,
 *    this list of conditions and the following disclaimer.
 *
 * 2. Redistributions in binary form must reproduce the above copyright notice,
 *    this list of conditions and the following disclaimer in the documentation
 *    and/or other materials provided with the distribution.
 *
 * 3. Neither the name of the copyright holder nor the names of its
 *    contributors may be used to endorse or promote products derived from this
 *    software without specific prior written permission.
 *
 * THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
 * AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
 * IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
 * DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE
 * FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL
 * DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
 * SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
 * CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY,
 * OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
 * OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
 */

/**
 * Filter Module - Manages hiding TinyOlly's own telemetry
 */

let hideTinyOlly = true;

// Load state from localStorage
try {
    const savedState = localStorage.getItem('tinyolly-hide-self');
    hideTinyOlly = savedState !== null ? savedState === 'true' : true;
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
 * Check if a service name is a TinyOlly internal service
 */
function isTinyOllyService(serviceName) {
    if (!serviceName) return false;
    // Only filter the core TinyOlly services, not infrastructure like Redis
    return serviceName === 'tinyolly-ui' ||
           serviceName === 'tinyolly-otlp-receiver' ||
           serviceName === 'tinyolly-opamp-server';
}

/**
 * Filter function to exclude TinyOlly internal services
 */
export function filterTinyOllyData(item) {
    if (!hideTinyOlly) return true;

    // Check various service name fields
    const serviceName = item.service_name ||
                       item.serviceName ||
                       item.service ||
                       item.name ||
                       item.id ||  // For service map nodes
                       (item.attributes && (
                           item.attributes['service.name'] ||
                           item.attributes.service_name
                       )) ||
                       (item.resource && item.resource['service.name']);

    // Filter out TinyOlly internal services
    return !isTinyOllyService(serviceName);
}

/**
 * Filter traces - exclude if service is a TinyOlly internal service
 */
export function filterTinyOllyTrace(trace) {
    if (!hideTinyOlly) return true;

    // API returns service_name field for traces
    const serviceName = trace.service_name || trace.serviceName || trace.root_service || trace.rootService;
    return !isTinyOllyService(serviceName);
}

/**
 * Filter metrics - exclude if only from TinyOlly internal services
 */
export function filterTinyOllyMetric(metric) {
    if (!hideTinyOlly) return true;

    // Check services array (from metrics list endpoint)
    if (metric.services && Array.isArray(metric.services)) {
        // Filter out if ALL services are TinyOlly internal services
        const hasNonTinyOllyService = metric.services.some(service => !isTinyOllyService(service));
        return hasNonTinyOllyService;
    }

    // Check in resources object (for single metric detail)
    if (metric.resources) {
        const serviceName = metric.resources['service.name'];
        if (isTinyOllyService(serviceName)) return false;
    }

    // Check in series (for metric detail view)
    if (metric.series && Array.isArray(metric.series)) {
        // Filter out entire metric if all series are from TinyOlly services
        const nonTinyOllySeries = metric.series.filter(s => {
            const serviceName = s.resources && s.resources['service.name'];
            return !isTinyOllyService(serviceName);
        });
        return nonTinyOllySeries.length > 0;
    }

    return true;
}

/**
 * Filter metric series - exclude series from TinyOlly internal services
 */
export function filterTinyOllyMetricSeries(series) {
    if (!hideTinyOlly) return series;

    return series.filter(s => {
        const serviceName = s.resources && s.resources['service.name'];
        return !isTinyOllyService(serviceName);
    });
}
