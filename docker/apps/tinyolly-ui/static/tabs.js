/**
 * Tabs Module - Manages tab switching, auto-refresh, and browser history
 */
import { loadLogs, loadSpans, loadTraces, loadMetrics, loadServiceMap, loadServiceCatalog } from './api.js';
import { showTracesList, isSpanDetailOpen } from './render.js';

let currentTab = 'traces';
let autoRefreshInterval = null;
let autoRefreshEnabled = true;
let tabPauseStates = {
    logs: false,
    metrics: false,
    traces: false
};
try {
    autoRefreshEnabled = localStorage.getItem('tinyolly-auto-refresh') !== 'false';
    const savedPauseStates = localStorage.getItem('tinyolly-tab-pause-states');
    if (savedPauseStates) {
        tabPauseStates = JSON.parse(savedPauseStates);
    }
} catch (e) {
    console.warn('LocalStorage access failed:', e);
}

export function initTabs() {
    let savedTab = 'logs';
    try {
        savedTab = localStorage.getItem('tinyolly-active-tab') || 'logs';
    } catch (e) { console.warn('LocalStorage access failed:', e); }
    switchTab(savedTab, null, true); // true = initial load, don't push to history
    updateAutoRefreshButton();
    updateTabPauseButtons();

    // Handle browser back/forward buttons
    window.addEventListener('popstate', (event) => {
        if (event.state && event.state.tab) {
            switchTab(event.state.tab, null, true); // true = from history, don't push again
        }
    });
}

export function switchTab(tabName, element, fromHistory = false) {
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
}

export function startAutoRefresh() {
    stopAutoRefresh();

    autoRefreshInterval = setInterval(() => {
        // Don't refresh if a span detail is open
        if (currentTab === 'spans' && isSpanDetailOpen()) {
            return;
        }

        // Don't refresh metrics if a chart is open or tab is paused
        if (currentTab === 'metrics') {
            if (tabPauseStates.metrics) {
                return;
            }
            import('./metrics.js').then(module => {
                if (module.isMetricChartOpen && module.isMetricChartOpen()) {
                    return;
                } else {
                    loadMetrics();
                }
            });
        } else if (currentTab === 'traces' && !document.getElementById('trace-detail-view').style.display.includes('block')) {
            if (!tabPauseStates.traces) {
                loadTraces();
            }
        } else if (currentTab === 'spans') {
            import('./spans.js').then(spansModule => {
                const serviceFilter = spansModule.getServiceFilter ? spansModule.getServiceFilter() : null;
                loadSpans(serviceFilter);
            });
        } else if (currentTab === 'logs') {
            if (tabPauseStates.logs) {
                return;
            }
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
        }

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

function updateTabPauseButtons() {
    updateTabPauseButton('logs');
    updateTabPauseButton('metrics');
    updateTabPauseButton('traces');
}

function updateTabPauseButton(tabName) {
    const btn = document.getElementById(`${tabName}-pause-btn`);
    const icon = document.getElementById(`${tabName}-pause-icon`);

    if (!btn || !icon) return;

    const isPaused = tabPauseStates[tabName];
    if (isPaused) {
        icon.textContent = '▶';
        btn.title = 'Resume auto-refresh for this tab';
        btn.style.background = '#6b7280';
    } else {
        icon.textContent = '⏸';
        btn.title = 'Pause auto-refresh for this tab';
        btn.style.background = 'var(--primary)';
    }
}

function saveTabPauseStates() {
    try {
        localStorage.setItem('tinyolly-tab-pause-states', JSON.stringify(tabPauseStates));
    } catch (e) {
        console.warn('LocalStorage access failed:', e);
    }
}

window.toggleLogsPause = function() {
    tabPauseStates.logs = !tabPauseStates.logs;
    saveTabPauseStates();
    updateTabPauseButton('logs');
};

window.toggleMetricsPause = function() {
    tabPauseStates.metrics = !tabPauseStates.metrics;
    saveTabPauseStates();
    updateTabPauseButton('metrics');
};

window.toggleTracesPause = function() {
    tabPauseStates.traces = !tabPauseStates.traces;
    saveTabPauseStates();
    updateTabPauseButton('traces');
};
