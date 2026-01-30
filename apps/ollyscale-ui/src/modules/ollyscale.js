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

import { initTabs, startAutoRefresh, switchTab, toggleAutoRefresh } from './tabs.js';
import { loadLogs, loadSpans } from './api.js';
import { initTheme, toggleTheme } from './theme.js';
import { initNamespaceFilter, startNamespaceRefresh } from './namespaceFilter.js';
import {
    showTraceDetail,
    showTracesList,
    toggleTraceJSON,
    copyTraceJSON,
    downloadTraceJSON,
    showLogsForTrace,
    clearLogFilter,
    filterLogs
} from './render.js';

import { clearTraceFilter, filterTraces } from './traces.js';
import { clearSpanFilter, filterSpans } from './spans.js';
import { filterMetrics } from './metrics.js';

import { debounce } from './utils.js';

// Expose functions globally for HTML onclick handlers
window.switchTab = switchTab;
window.toggleTheme = toggleTheme;
window.toggleAutoRefresh = toggleAutoRefresh;
window.showTraceDetail = showTraceDetail;
window.showTracesList = showTracesList;
window.toggleTraceJSON = toggleTraceJSON;
window.copyTraceJSON = copyTraceJSON;
window.downloadTraceJSON = downloadTraceJSON;
window.showLogsForTrace = showLogsForTrace;
window.loadLogs = loadLogs;
window.loadSpans = loadSpans;
window.clearLogFilter = clearLogFilter;
window.filterLogs = filterLogs;
window.clearTraceFilter = clearTraceFilter;
window.clearSpanFilter = clearSpanFilter;
window.filterSpans = filterSpans;

// Global error handler
window.onerror = function (message, source, lineno, colno, error) {
    console.error('Global error caught:', message, error);
    return false;
};

// Initialize after DOM is ready
document.addEventListener('DOMContentLoaded', () => {
    try {
        initTheme();
        initNamespaceFilter();

        // Tab initialization now handles URL parameters internally
        initTabs();

        // Start namespace auto-refresh (60 second interval)
        startNamespaceRefresh();

        // Attach log search event listener with debounce
        const logSearch = document.getElementById('log-search');
        if (logSearch) {
            logSearch.addEventListener('keyup', debounce(filterLogs, 300));
        }

        // Attach span search event listener with debounce
        const spanSearch = document.getElementById('span-search');
        if (spanSearch) {
            spanSearch.addEventListener('keyup', debounce(filterSpans, 300));
        }

        // Attach trace search event listener with debounce
        const traceSearch = document.getElementById('trace-search');
        if (traceSearch) {
            traceSearch.addEventListener('keyup', debounce(filterTraces, 300));
        }

        // Attach metric search event listener with debounce
        const metricSearch = document.getElementById('metric-search');
        if (metricSearch) {
            metricSearch.addEventListener('keyup', debounce(filterMetrics, 300));
        }

        if (localStorage.getItem('ollyscale-auto-refresh') !== 'false') {
            startAutoRefresh();
        }
    } catch (error) {
        console.error('Error during initialization:', error);
    }
});
