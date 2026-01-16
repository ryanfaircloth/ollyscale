/**
 * BSD 3-Clause License
 *
 * Copyright (c) 2025, Infrastructure Architects, LLC
 * All rights reserved.
 */

// Import styles
import './styles/main.css';

// Import Cytoscape for service map
import cytoscape from 'cytoscape';

// Import Chart.js for metrics
import { Chart, registerables } from 'chart.js';

// Register Chart.js components
Chart.register(...registerables);

// Make libraries globally available
(window as any).cytoscape = cytoscape;
(window as any).Chart = Chart;

// Import all application modules
import './modules/api.js';
import './modules/theme.js';
import './modules/tabs.js';
import './modules/filter.js';
import './modules/utils.js';
import './modules/render.js';
import './modules/logs.js';
import './modules/traces.js';
import './modules/spans.js';
import './modules/metrics.js';
import './modules/serviceCatalog.js';
import './modules/serviceMap.js';
import './modules/aiAgents.js';
import './modules/collector.js';
import './modules/ollyscale.js';

console.log('[OllyScale] Application initialized');
console.log('[OllyScale] Cytoscape version:', cytoscape.version);
console.log('[OllyScale] Chart.js version:', Chart.version);
