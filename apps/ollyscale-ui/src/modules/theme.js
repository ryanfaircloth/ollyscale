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
 * Theme Module - Manages light/dark theme switching and persistence
 */
import { loadMetrics, loadServiceMap } from './api.js';

export function initTheme() {
    let savedTheme = 'light';
    try {
        savedTheme = localStorage.getItem('tinyolly-theme');
    } catch (e) {
        console.warn('LocalStorage access failed:', e);
    }
    if (savedTheme === 'dark' || (!savedTheme && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
        setTheme('dark');
    } else {
        setTheme('light');
    }
}

export function toggleTheme() {
    const currentTheme = document.documentElement.getAttribute('data-theme');
    const newTheme = currentTheme === 'dark' ? 'light' : 'dark';
    setTheme(newTheme);
}

export function setTheme(theme) {
    document.documentElement.setAttribute('data-theme', theme);
    try {
        localStorage.setItem('tinyolly-theme', theme);
    } catch (e) { console.warn('LocalStorage access failed:', e); }

    const icon = document.getElementById('theme-icon');
    const text = document.getElementById('theme-text');

    if (theme === 'dark') {
        icon.textContent = '☀️';
        text.textContent = 'Light Mode';
    } else {
        icon.textContent = '🌙';
        text.textContent = 'Dark Mode';
    }

    // Re-render charts if they exist (to update colors)
    // We need to import currentTab from somewhere or pass it in,
    // but for now let's rely on the global currentTab if possible or just re-render active tab
    const activeTab = localStorage.getItem('tinyolly-active-tab');
    if (activeTab === 'map') {
        loadServiceMap();
    } else if (activeTab === 'metrics') {
        // Only reload metrics if metrics tab is actually visible
        const metricsTab = document.getElementById('metrics-content');
        if (metricsTab && metricsTab.classList.contains('active')) {
            loadMetrics();
        }
    }
}
