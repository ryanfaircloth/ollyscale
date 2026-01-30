/*
 * Namespace Filter Module
 * Copyright (c) 2026 Ryan Faircloth
 * AGPL-3.0 License
 */

/**
 * Namespace filtering with multi-select dropdown
 */

let allNamespaces = [];
let selectedNamespaces = new Set();
let userHasMadeSelection = false;
let lastFetchTime = 0;
const CACHE_DURATION_MS = 60000; // 1 minute

/**
 * Initialize namespace filter
 */
export async function initNamespaceFilter() {
    await fetchNamespaces();
    renderNamespaceDropdown();
    loadSelectionState();
}

/**
 * Fetch namespaces from API
 */
async function fetchNamespaces() {
    const now = Date.now();

    // Use cache if less than 1 minute old
    if (allNamespaces.length > 0 && (now - lastFetchTime) < CACHE_DURATION_MS) {
        return;
    }

    try {
        const response = await fetch('/api/namespaces');
        if (!response.ok) {
            console.error('Failed to fetch namespaces:', response.statusText);
            return;
        }

        const data = await response.json();
        const newNamespaces = data.namespaces || [];

        // Sort case-insensitive
        newNamespaces.sort((a, b) => {
            const aLower = a.toLowerCase();
            const bLower = b.toLowerCase();
            return aLower.localeCompare(bLower);
        });

        // Handle new namespaces
        const existingSet = new Set(allNamespaces);
        const addedNamespaces = newNamespaces.filter(ns => !existingSet.has(ns));

        allNamespaces = newNamespaces;
        lastFetchTime = now;

        // Apply default selection logic for new namespaces
        if (addedNamespaces.length > 0) {
            for (const ns of addedNamespaces) {
                if (userHasMadeSelection) {
                    // User has made selections - new items default to unselected
                    selectedNamespaces.delete(ns);
                } else {
                    // User hasn't made selections - select all except "ollyscale"
                    if (ns !== 'ollyscale') {
                        selectedNamespaces.add(ns);
                    }
                }
            }
        }

        // Initial selection if no user interaction yet
        if (!userHasMadeSelection && selectedNamespaces.size === 0) {
            for (const ns of allNamespaces) {
                if (ns !== 'ollyscale') {
                    selectedNamespaces.add(ns);
                }
            }
        }

        renderNamespaceDropdown();
        saveSelectionState();
    } catch (error) {
        console.error('Error fetching namespaces:', error);
    }
}

/**
 * Render namespace dropdown
 */
function renderNamespaceDropdown() {
    const container = document.getElementById('namespace-filter-container');
    if (!container) return;

    const selectedCount = selectedNamespaces.size;
    const totalCount = allNamespaces.length;
    const buttonText = selectedCount === totalCount ? 'All Namespaces' : `${selectedCount}/${totalCount} Namespaces`;

    container.innerHTML = `
        <div class="namespace-filter">
            <button id="namespace-filter-btn" class="namespace-filter-button">
                ${buttonText} ▼
            </button>
            <div id="namespace-dropdown" class="namespace-dropdown" style="display: none;">
                <div class="namespace-dropdown-header">
                    <button id="namespace-select-all" class="namespace-action-btn">Select All</button>
                    <button id="namespace-deselect-all" class="namespace-action-btn">Deselect All</button>
                </div>
                <div class="namespace-list">
                    ${allNamespaces.map(ns => `
                        <label class="namespace-item">
                            <input type="checkbox" value="${ns}" ${selectedNamespaces.has(ns) ? 'checked' : ''}>
                            <span>${ns || '(no namespace)'}</span>
                        </label>
                    `).join('')}
                </div>
            </div>
        </div>
    `;

    // Attach event listeners
    document.getElementById('namespace-filter-btn').onclick = toggleDropdown;
    document.getElementById('namespace-select-all').onclick = selectAll;
    document.getElementById('namespace-deselect-all').onclick = deselectAll;

    const checkboxes = document.querySelectorAll('.namespace-item input[type="checkbox"]');
    checkboxes.forEach(cb => {
        cb.onchange = handleCheckboxChange;
    });

    // Close dropdown when clicking outside
    document.addEventListener('click', handleClickOutside);
}

/**
 * Toggle dropdown visibility
 */
function toggleDropdown(e) {
    e.stopPropagation();
    const dropdown = document.getElementById('namespace-dropdown');
    if (dropdown) {
        dropdown.style.display = dropdown.style.display === 'none' ? 'block' : 'none';
    }
}

/**
 * Handle checkbox change
 */
function handleCheckboxChange(e) {
    const namespace = e.target.value;
    userHasMadeSelection = true;

    if (e.target.checked) {
        selectedNamespaces.add(namespace);
    } else {
        selectedNamespaces.delete(namespace);
    }

    saveSelectionState();
    renderNamespaceDropdown();

    // Trigger data reload
    reloadCurrentView();
}

/**
 * Select all namespaces
 */
function selectAll(e) {
    e.stopPropagation();
    userHasMadeSelection = true;
    selectedNamespaces = new Set(allNamespaces);
    saveSelectionState();
    renderNamespaceDropdown();
    reloadCurrentView();
}

/**
 * Deselect all namespaces
 */
function deselectAll(e) {
    e.stopPropagation();
    userHasMadeSelection = true;
    selectedNamespaces.clear();
    saveSelectionState();
    renderNamespaceDropdown();
    reloadCurrentView();
}

/**
 * Handle clicks outside dropdown
 */
function handleClickOutside(e) {
    const dropdown = document.getElementById('namespace-dropdown');
    const button = document.getElementById('namespace-filter-btn');

    if (dropdown && button && !button.contains(e.target) && !dropdown.contains(e.target)) {
        dropdown.style.display = 'none';
    }
}

/**
 * Get current namespace filter for API
 * Returns array of Filter objects with OR logic
 */
export function getNamespaceFilters() {
    console.log('[DEBUG getNamespaceFilters] allNamespaces:', allNamespaces, 'selectedNamespaces:', Array.from(selectedNamespaces));

    // If no namespaces fetched yet, don't filter - show everything
    if (allNamespaces.length === 0) {
        console.log('[DEBUG getNamespaceFilters] No namespaces loaded yet, returning null (no filter)');
        return null;
    }

    if (selectedNamespaces.size === 0 || selectedNamespaces.size === allNamespaces.length) {
        console.log('[DEBUG getNamespaceFilters] All/none selected, returning null');
        return null; // No filter needed - either none selected or all selected
    }

    // Build filters for selected namespaces
    // These will be OR'd together as a group
    const filters = Array.from(selectedNamespaces).map(ns => ({
        field: 'service_namespace',
        operator: 'equals',
        value: ns
    }));
    console.log('[DEBUG getNamespaceFilters] Returning filters:', filters);
    return filters;
}

/**
 * Save selection state to localStorage
 */
function saveSelectionState() {
    try {
        localStorage.setItem('namespace-filter-selection', JSON.stringify({
            selected: Array.from(selectedNamespaces),
            userHasMadeSelection: userHasMadeSelection
        }));
    } catch (e) {
        console.warn('Failed to save namespace selection:', e);
    }
}

/**
 * Load selection state from localStorage
 */
function loadSelectionState() {
    try {
        const saved = localStorage.getItem('namespace-filter-selection');
        if (saved) {
            const state = JSON.parse(saved);
            selectedNamespaces = new Set(state.selected);
            userHasMadeSelection = state.userHasMadeSelection;
            renderNamespaceDropdown();
        }
    } catch (e) {
        console.warn('Failed to load namespace selection:', e);
    }
}

/**
 * Reload current view after filter change
 */
function reloadCurrentView() {
    import('./tabs.js').then(module => {
        const currentTab = module.getCurrentTab ? module.getCurrentTab() : 'logs';
        if (currentTab === 'logs') {
            import('./api.js').then(api => api.loadLogs());
        } else if (currentTab === 'traces') {
            import('./api.js').then(api => api.loadTraces());
        } else if (currentTab === 'metrics') {
            import('./api.js').then(api => api.loadMetrics());
        }
    });
}

/**
 * Start periodic namespace refresh
 */
export function startNamespaceRefresh() {
    setInterval(fetchNamespaces, CACHE_DURATION_MS);
}
