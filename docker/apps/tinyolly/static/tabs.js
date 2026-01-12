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
 * Tabs Module - Manages tab switching, auto-refresh, and browser history
 */
import { loadLogs, loadSpans, loadTraces, loadMetrics, loadServiceMap, loadServiceCatalog, loadCollector, initCollector } from './api.js';
import { showTracesList, isSpanDetailOpen } from './render.js';
import { clearMetricSearch } from './metrics.js';

let currentTab = 'traces';
let autoRefreshInterval = null;
let autoRefreshEnabled = true;
try {
    autoRefreshEnabled = localStorage.getItem('tinyolly-auto-refresh') !== 'false';
} catch (e) {
    console.warn('LocalStorage access failed:', e);
}

export function getCurrentTab() {
    return currentTab;
}

export function initTabs() {
    // Check URL parameter first (for bookmarks/direct links)
    const urlParams = new URLSearchParams(window.location.search);
    const urlTab = urlParams.get('tab');

    // Always default to 'logs' tab when opening the base URL
    // Only use URL parameter if explicitly provided
    const savedTab = urlTab || 'logs';

    switchTab(savedTab, null, true); // true = initial load, don't push to history
    updateAutoRefreshButton();

    // Handle browser back/forward buttons
    window.addEventListener('popstate', (event) => {
        if (event.state && event.state.tab) {
            switchTab(event.state.tab, null, true); // true = from history, don't push again
        }
    });
}

export function switchTab(tabName, element, fromHistory = false) {
    // Clear metric search when leaving metrics tab
    if (currentTab === 'metrics' && tabName !== 'metrics') {
        clearMetricSearch();
    }

    currentTab = tabName;
    try {
        localStorage.setItem('tinyolly-active-tab', tabName);
    } catch (e) { console.warn('LocalStorage access failed:', e); }

    // Update browser history (only if not from history navigation)
    if (!fromHistory) {
        const url = new URL(window.location);
        url.searchParams.set('tab', tabName);
        window.history.pushState({ tab: tabName }, '', url);
    }

    // Update tab buttons
    document.querySelectorAll('.tab').forEach(t => t.classList.remove('active'));
    if (element) {
        element.classList.add('active');
    } else {
        const btn = document.querySelector(`.tab[data-tab="${tabName}"]`);
        if (btn) btn.classList.add('active');
    }

    // Update tab content
    document.querySelectorAll('.tab-content').forEach(c => c.classList.remove('active'));

    const contentId = `${tabName}-content`;
    const contentDiv = document.getElementById(contentId);
    if (contentDiv) {
        contentDiv.classList.add('active');
    }

    // Load data
    if (tabName === 'logs') loadLogs();
    else if (tabName === 'spans') {
        import('./spans.js').then(spansModule => {
            const serviceFilter = spansModule.getServiceFilter ? spansModule.getServiceFilter() : null;
            loadSpans(serviceFilter);
        });
    }
    else if (tabName === 'traces') {
        // Reset to list view when switching to traces tab
        showTracesList();
    }
    else if (tabName === 'metrics') loadMetrics();
    else if (tabName === 'catalog') loadServiceCatalog();
    else if (tabName === 'map') loadServiceMap();
    else if (tabName === 'collector') {
        initCollector();
        loadCollector();
    }
    else if (tabName === 'ai-agents') {
        import('./aiAgents.js').then(module => module.loadAISessions());
    }
}

export function startAutoRefresh() {
    stopAutoRefresh();

    autoRefreshInterval = setInterval(() => {
        // Don't refresh if a span detail is open
        if (currentTab === 'spans' && isSpanDetailOpen()) {
            return;
        }

        // Don't refresh metrics if a chart is open
        if (currentTab === 'metrics') {
            import('./metrics.js').then(module => {
                if (module.isMetricChartOpen && module.isMetricChartOpen()) {
                    return;
                } else {
                    loadMetrics();
                }
            });
        } else if (currentTab === 'traces' && !document.getElementById('trace-detail-view').style.display.includes('block')) {
            loadTraces();
        } else if (currentTab === 'spans') {
            import('./spans.js').then(spansModule => {
                const serviceFilter = spansModule.getServiceFilter ? spansModule.getServiceFilter() : null;
                loadSpans(serviceFilter);
            });
        } else if (currentTab === 'logs') {
            import('./render.js').then(module => {
                if (module.isLogJsonOpen && module.isLogJsonOpen()) {
                    return;
                } else {
                    loadLogs();
                }
            });
        } else if (currentTab === 'catalog') {
            loadServiceCatalog();
        } else if (currentTab === 'map') {
            loadServiceMap();
        } else if (currentTab === 'ai-agents') {
            import('./aiAgents.js').then(module => {
                // Don't refresh if JSON view is open or detail view is open
                if (module.isAISessionJsonOpen && module.isAISessionJsonOpen()) {
                    return;
                }
                if (document.getElementById('ai-detail-view').style.display.includes('block')) {
                    return;
                }
                module.loadAISessions();
            });
        }
        // Don't auto-refresh collector tab - user is editing config

        // Also refresh stats
        import('./api.js').then(module => module.loadStats());

    }, 5000);
}

export function stopAutoRefresh() {
    if (autoRefreshInterval) {
        clearInterval(autoRefreshInterval);
        autoRefreshInterval = null;
    }
}

export function toggleAutoRefresh() {
    autoRefreshEnabled = !autoRefreshEnabled;
    try {
        localStorage.setItem('tinyolly-auto-refresh', autoRefreshEnabled);
    } catch (e) { console.warn('LocalStorage access failed:', e); }

    if (autoRefreshEnabled) {
        startAutoRefresh();
    } else {
        stopAutoRefresh();
    }
    updateAutoRefreshButton();
}

function updateAutoRefreshButton() {
    const btn = document.getElementById('auto-refresh-btn');
    const icon = document.getElementById('refresh-icon');

    if (!btn || !icon) return;

    if (autoRefreshEnabled) {
        icon.textContent = '⏸';
        btn.title = 'Pause auto-refresh';
        btn.style.background = 'var(--primary)';
    } else {
        icon.textContent = '▶';
        btn.title = 'Resume auto-refresh';
        btn.style.background = '#6b7280';
    }
}

