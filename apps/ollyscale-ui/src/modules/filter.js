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
 * Filter Module - Manages hiding OllyScale's own telemetry
 */

let hideOllyScale = true;

// Load state from localStorage
try {
    const savedState = localStorage.getItem('ollyscale-hide-self');
    hideOllyScale = savedState !== null ? savedState === 'true' : true;
} catch (e) {
    console.warn('LocalStorage access failed:', e);
}

export function initHideOllyScaleToggle() {
    updateHideOllyScaleButton();
}

export function toggleHideOllyScale() {
    hideOllyScale = !hideOllyScale;
    try {
        localStorage.setItem('ollyscale-hide-self', hideOllyScale);
    } catch (e) {
        console.warn('LocalStorage access failed:', e);
    }
    updateHideOllyScaleButton();

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

function updateHideOllyScaleButton() {
    const btn = document.getElementById('hide-ollyscale-btn');
    const text = document.getElementById('hide-ollyscale-text');

    if (!btn || !text) return;

    if (hideOllyScale) {
        text.textContent = 'Show OllyScale';
        btn.title = 'OllyScale telemetry is hidden - click to show';
    } else {
        text.textContent = 'Hide OllyScale';
        btn.title = 'OllyScale telemetry is visible - click to hide';
    }
}

/**
 * Check if OllyScale telemetry should be hidden
 */
export function shouldHideOllyScale() {
    return hideOllyScale;
}

/**
 * Check if a service name is an OllyScale internal service
 */
function isOllyScaleService(serviceName) {
    if (!serviceName) return false;
    // Only filter the core OllyScale services, not infrastructure like Redis
    return serviceName === 'ollyscale-ui' ||
           serviceName === 'ollyscale-otlp-receiver' ||
           serviceName === 'ollyscale-opamp-server';
}

/**
 * Filter function to exclude OllyScale internal services
 */
export function filterOllyScaleData(item) {
    if (!hideOllyScale) return true;

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

    // Filter out ollyScale internal services
    return !isOllyScaleService(serviceName);
}

/**
 * Filter traces - exclude if service is a ollyScale internal service
 */
export function filterOllyScaleTrace(trace) {
    if (!hideollyScale) return true;

    // API returns service_name field for traces
    const serviceName = trace.service_name || trace.serviceName || trace.root_service || trace.rootService;
    return !isOllyScaleService(serviceName);
}

/**
 * Filter metrics - exclude if only from ollyScale internal services
 */
export function filterOllyScaleMetric(metric) {
    if (!hideollyScale) return true;

    // Check services array (from metrics list endpoint)
    if (metric.services && Array.isArray(metric.services)) {
        // Filter out if ALL services are ollyScale internal services
        const hasNonollyScaleService = metric.services.some(service => !isOllyScaleService(service));
        return hasNonollyScaleService;
    }

    // Check in resources object (for single metric detail)
    if (metric.resources) {
        const serviceName = metric.resources['service.name'];
        if (isOllyScaleService(serviceName)) return false;
    }

    // Check in series (for metric detail view)
    if (metric.series && Array.isArray(metric.series)) {
        // Filter out entire metric if all series are from ollyScale services
        const nonollyScaleSeries = metric.series.filter(s => {
            const serviceName = s.resources && s.resources['service.name'];
            return !isOllyScaleService(serviceName);
        });
        return nonollyScaleSeries.length > 0;
    }

    return true;
}

/**
 * Filter metric series - exclude series from ollyScale internal services
 */
export function filterOllyScaleMetricSeries(series) {
    if (!hideollyScale) return series;

    return series.filter(s => {
        const serviceName = s.resources && s.resources['service.name'];
        return !isOllyScaleService(serviceName);
    });
}
