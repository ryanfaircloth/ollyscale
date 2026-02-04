# React UI Implementation Plan - ollyScale v3

> **📊 CURRENT STATUS (2026-02-01)**:
>
> **✅ Phases 1-6, 9, 10.2 (Basic), 10.3 COMPLETE**: Core UI with i18n and browser telemetry deployed
>
> - **Apps deployed**:
>   - ✅ ollyscale-webui (React UI)
>   - ✅ ollyscale-legacyui (old UI for comparison)
>   - ✅ ollyscale-api (PostgreSQL backend)
>   - ✅ ollyscale-browser-collector (browser telemetry collector)
>
> - **Key Features Working**:
>   - ✅ All 9 pages (Dashboard, Traces, Spans, Logs, Metrics, Services, Service Map, AI Agents stub, Collector Config stub)
>   - ✅ Service Map with icons (PostgreSQL, MySQL, MongoDB, Redis, Kafka, RabbitMQ, Nginx)
>   - ✅ Auto-refresh with sliding time window (LIVE/PAUSED mode)
>   - ✅ Query builder with filters and presets
>   - ✅ Charts and visualizations (Chart.js, Cytoscape)
>   - ✅ Dark/light theme support
>   - ✅ **Internationalization (i18n)** - 287 translation keys, en-US/en-GB, LanguageSelector component
>   - ✅ **Browser Telemetry (Basic)** - Auto-instrumented traces for page loads, interactions, API calls
>
> - **Priority Enhancements Needed** (See "Priority Next Steps" at end):
>   - 🔄 **Browser Telemetry Enhancements** (Priority 1): Add error handlers, ErrorBoundary, custom events
>   - 🔄 **Testing** (Priority 2): Infrastructure installed, need tests written (only 1 test file exists)
>   - 🔄 **AI Agents** (Priority 3): GenAI span visualization with token tracking
>   - 🔄 **OTel Config** (Priority 4): OpAMP integration for collector management
>
> - **Next Steps**: See "Priority Next Steps" section at end of document
>
> **⚠️ NOTE**: Prior status files (react-ui-decisions.md, react-ui-implementation-status.md) were outdated and have been removed. This plan is now the single source of truth.
>
> **Last Verified**: 2026-02-01 (after i18n implementation and status verification)

## Overview

This plan outlines the complete migration from the current Vanilla JS/TypeScript UI (`apps/ollyscale-ui`) to a modern React-based UI with Bootstrap styling, advanced query builder, and embedded documentation.

## Goals

1. **Framework Migration**: Replace Vanilla JS with React for better state management and component reusability
2. **UI Framework**: Implement Bootstrap for consistent, professional styling
3. **Query Builder**: Replace simple text filters with a visual query builder for complex filtering
4. **Embedded Documentation**: Move documentation into the product for better user experience
5. **Functional Parity**: Maintain all existing features from the current UI
6. **Code Cleanup**: Remove TinyOlly legacy code as part of the redesign

## Technology Stack

### Core

- **React 18+**: Modern React with hooks
- **TypeScript**: Type safety and better developer experience
- **Vite**: Fast build tooling (already in use)

### UI Framework

- **React Bootstrap**: Bootstrap 5 components for React
- **Bootstrap Icons**: Consistent icon set
- **React Router**: Client-side routing

### Query Builder

✅ **PARTIALLY IMPLEMENTED**

- **react-querybuilder**: Advanced query builder component (INSTALLED)
- Custom query builder components built (QueryBuilder, CompactQueryBuilder, EnhancedQueryBuilder)
- Custom operators for OTLP field types (CUSTOM IMPLEMENTATION, not using react-querybuilder library features)
- Field schemas defined for traces, spans, logs, metrics
- ❌ NOT using react-querybuilder's built-in UI components
- ❌ Visual query builder UI not implemented (using custom compact version)
- ❌ Save/load filter presets not implemented

### State Management

- **React Context API**: Global state (theme, namespace filters)
- **TanStack Query (React Query)**: Server state management, caching, auto-refresh

### Charts & Visualization

- **Recharts**: React-based charting library (replaces Chart.js)
- **React Cytoscape**: Service map visualization (replaces Cytoscape.js direct usage)

### Browser Telemetry

✅ **BASIC IMPLEMENTATION COMPLETE** (2026-01-30)
🔄 **ENHANCEMENTS NEEDED** (error handling, custom events)

- **@opentelemetry/api** 1.9.0: OpenTelemetry API (INSTALLED)
- **@opentelemetry/sdk-trace-web** 2.5.0: Browser tracing SDK (INSTALLED)
- **@opentelemetry/auto-instrumentations-web** 0.56.0: Auto-instrumentation meta-package (INSTALLED)
  - ✅ Document load instrumentation (page performance)
  - ✅ User interaction instrumentation (clicks, form submits)
  - ✅ Fetch/XHR instrumentation (API call tracing)
- **@opentelemetry/exporter-trace-otlp-http** 0.211.0: OTLP HTTP exporter (INSTALLED)
- **@opentelemetry/semantic-conventions** 1.39.0: Semantic conventions (INSTALLED)
- **Implementation Status**:
  - ✅ src/telemetry/config.ts - Provider, exporter, consent checking
  - ✅ src/telemetry/instrumentations.ts - Auto-instrumentations configuration
  - ✅ ConsentBanner component for GDPR compliance
  - ✅ useTracing hook with startSpan, recordError, addEvent helpers
  - ✅ OpenTelemetryCollector CR deployed (ollyscale-browser-collector)
  - ✅ HTTPRoute configured for /v1/traces with proper routing
  - ❌ Global error handler (window.onerror) - NOT IMPLEMENTED
  - ❌ Promise rejection handler (window.onunhandledrejection) - NOT IMPLEMENTED
  - ❌ ErrorBoundary component for React errors - NOT IMPLEMENTED
  - ❌ Custom business events - NOT IMPLEMENTED

### Internationalization

✅ **FULLY IMPLEMENTED** (2026-02-01, commit 1a166f2)

- **react-i18next**: Translation management (INSTALLED v15.2.0)
- **i18next**: Core i18n library (INSTALLED v24.2.2)
- **i18next-browser-languagedetector**: Auto-detect browser language (INSTALLED v8.0.2)
🔄 **INFRASTRUCTURE INSTALLED, TESTS NEEDED**

- **Vitest** 4.0.18: Fast unit testing (INSTALLED)
- **@vitest/ui**: Vitest UI for test runner (INSTALLED)
- **React Testing Library** 16.3.2: Component testing (INSTALLED)
- **@testing-library/jest-dom** 6.9.1: Custom matchers (INSTALLED)
- **@testing-library/user-event** 14.6.1: User interaction simulation (INSTALLED)
- **MSW (Mock Service Worker)**: API mocking (❌ NOT INSTALLED YET)
- **Playwright**: E2E testing (❌ NOT INSTALLED, optional)
- **Test Files**: Only 1 test file exists (useDebounce.test.ts with 4 test cases)
- **Test Configuration**: ✅ vitest.config.ts exists, scripts in package.json
- **Coverage Goal**: 80%+ (currently near 0%)ish, French, German, Japanese

### Testing

❌ **NOT IMPLEMENTED YET**

- **Vitest**: Fast unit testing (NOT INSTALLED)
- **React Testing Library**: Component testing (NOT INSTALLED)
- **@testing-library/jest-dom**: Custom matchers (NOT INSTALLED)
- **@testing-library/user-event**: User interaction simulation (NOT INSTALLED)
- **MSW (Mock Service Worker)**: API mocking (NOT INSTALLED)
- **Playwright**: E2E testing (NOT INSTALLED)
- No test files exist (0 .test.ts or .test.tsx files)
- No test configuration
- No mocks or test utilities

### Code Quality

- **ESLint**: Linting with React rules
- **Prettier**: Code formatting
- **TypeScript**: Strict mode enabled

## Directory Structure

```
apps/react-ui/
├── package.json
├── tsconfig.json
├── vite.config.ts
├── index.html
├── public/
│   ├── manifest.json          # PWA manifest
│   ├── service-worker.js      # Basic service worker
│   └── assets/
│       ├── logo.svg
│       ├── favicon.ico
│       └── icons/             # PWA icons (192x192, 512x512)
│           ├── icon-192.png
│           └── icon-512.png
├── src/
│   ├── main.tsx                    # Entry point
│   ├── App.tsx                     # Root component
│   ├── vite-env.d.ts
│   ├── telemetry.ts                # OpenTelemetry browser setup
│   ├── i18n.ts                     # i18next configuration
│   │
│   ├── components/                 # Reusable components
│   │   ├── layout/
│   │   │   ├── AppLayout.tsx       # Main layout with sidebar
│   │   │   ├── Sidebar.tsx         # Navigation sidebar
│   │   │   ├── Header.tsx          # Top header (breadcrumbs, actions)
│   │   │   ├── Footer.tsx          # Footer
│   │   │   └── ConsentBanner.tsx   # GDPR telemetry consent
│   │   │
│   │   ├── common/
│   │   │   ├── LoadingSpinner.tsx
│   │   │   ├── ErrorBoundary.tsx
│   │   │   ├── EmptyState.tsx
│   │   │   ├── CopyButton.tsx
│   │   │   ├── DownloadButton.tsx
│   │   │   ├── RefreshButton.tsx
│   │   │   └── Badge.tsx
│   │   │
│   │   ├── query/
│   │   │   ├── QueryBuilder.tsx    # Main query builder
│   │   │   ├── FilterGroup.tsx     # Filter group (AND/OR)
│   │   │   ├── FilterRule.tsx      # Individual filter
│   │   │   ├── FieldSelector.tsx   # OTLP field dropdown
│   │   │   ├── OperatorSelector.tsx # eq, ne, contains, regex
│   │   │   └── ValueInput.tsx      # Value input with type hints
│   │   │
│   │   ├── telemetry/
│   │   │   ├── TraceCard.tsx       # Trace list item
│   │   │   ├── SpanCard.tsx        # Span list item
│   │   │   ├── LogCard.tsx         # Log entry
│   │   │   ├── MetricCard.tsx      # Metric display
│   │   │   ├── TraceWaterfall.tsx  # Trace waterfall view
│   │   │   ├── SpanDetail.tsx      # Span detail modal
│   │   │   ├── AttributeTable.tsx  # OTLP attributes
│   │   │   └── JsonViewer.tsx      # Pretty JSON viewer
│   │   │
│   │   └── docs/
│   │       ├── DocsSidebar.tsx     # Documentation sidebar
│   │       ├── DocsSearch.tsx      # Search docs
│   │       ├── DocContent.tsx      # Render markdown content
│   │       └── QuickHelp.tsx       # Context-sensitive help
│   │
│   ├── pages/                      # Page components
│   │   ├── TracesPage.tsx
│   │   ├── SpansPage.tsx
│   │   ├── LogsPage.tsx
│   │   ├── MetricsPage.tsx
│   │   ├── ServiceMapPage.tsx
│   │   ├── ServiceCatalogPage.tsx
│   │   ├── AIAgentsPage.tsx
│   │   ├── CollectorConfigPage.tsx
│   │   ├── DocsPage.tsx            # Embedded documentation
│   │   └── NotFoundPage.tsx
│   │
│   ├── features/                   # Feature-specific modules
│   │   ├── traces/
│   │   │   ├── hooks/
│   │   │   │   ├── useTraces.ts
│   │   │   │   ├── useTraceDetail.ts
│   │   │   │   └── useTraceFilters.ts
│   │   │   ├── components/
│   │   │   │   ├── TraceList.tsx
│   │   │   │   ├── TraceDetail.tsx
│   │   │   │   └── TraceFilters.tsx
│   │   │   └── types.ts
│   │   │
│   │   ├── spans/
│   │   ├── logs/
│   │   ├── metrics/
│   │   ├── services/
│   │   └── docs/
│   │
│   ├── api/                        # API client
│   │   ├── client.ts               # Base API client
│   │   ├── queries/                # React Query hooks
│   │   │   ├── useTracesQuery.ts
│   │   │   ├── useLogsQuery.ts
│   │   │   ├── useMetricsQuery.ts
│   │   │   ├── useServicesQuery.ts
│   │   │   └── useServiceMapQuery.ts
│   │   └── types/
│   │       ├── trace.ts
│   │       ├── log.ts
│   │       ├── metric.ts
│   │       └── service.ts
│   │
│   ├── contexts/                   # React contexts
│   │   ├── ThemeContext.tsx        # Dark/light theme
│   │   ├── DocsContext.tsx         # Documentation state
│   │   └── LanguageContext.tsx     # i18n language selection
│   │   ├── RefreshContext.tsx      # Auto-refresh control
│   │   └── DocsContext.tsx         # Documentation state
│   │
│   ├── hooks/                      # Custom hooks
│   │   ├── useAutoRefresh.ts       # Auto-refresh logic
│   │   ├── useLocalStorage.ts      # Persist state
│   │   ├── useDebounce.ts          # Debounce input
│   │   ├── useQuery.ts             # Query builder state
│   │   └── usePagination.ts        # Pagination logic
│   │
│   ├── utils/                      # Utility functions
│   │   ├── formatting.ts           # Time, duration, trace ID formatting
│   │   ├── otlp.ts                 # OTLP helpers
│   │   ├── validation.ts           # Form validation
│   │   └── constants.ts            # App constants
│   │
│   ├── styles/                     # Global styles
│   │   ├── main.scss               # Bootstrap customization
│   ├── locales/                    # Translation files
│   │   ├── en-US/
│   │   │   └── translation.json
│   │   └── en-GB/
│   │       └── translation.json
│   │   # Future: es, fr, de, ja
│   │
│   ├── __tests__/                  # Test files
│   │   ├── setup.ts                # Test setup
│   │   ├── mocks/                  # Mock data
│   │   ├── components/             # Component tests
│   │   ├── hooks/                  # Hook tests
│   │   └── integration/            # Integration tests
│   │
│   └── assets/                     # Static assets
│       └── docs/                   # Embedded docs (markdown)
│           ├── en-US/              # English US docs
│           │   ├── index.md
│           │   ├── quickstart.md
│           │   ├── traces.md
│           │   ├── logs.md
│           │   ├── metrics.md
│           │   └── api.md
│           └── en-GB/              # English GB docs (UK spelling)
│               # Future: es, fr, de, ja.md
│           ├── logs.md
│           ├── metrics.md
│           └── api.md
``OpenTelemetry Browser SDK
npm install @opentelemetry/api @opentelemetry/sdk-trace-web
npm install @opentelemetry/instrumentation-document-load
npm install @opentelemetry/instrumentation-user-interaction
npm install @opentelemetry/instrumentation-fetch
npm install @opentelemetry/instrumentation-xml-http-request
npm install @opentelemetry/exporter-trace-otlp-http
npm install @opentelemetry/resources @opentelemetry/semantic-conventions

# Internationalization
npm install react-i18next i18next i18next-browser-languagedetector

# Utilities
npm install date-fns clsx

# Dev Dependencies
npm install -D @types/react @types/react-dom
npm install -D @typescript-eslint/eslint-plugin @typescript-eslint/parser
npm install -D sass

# Testing
npm install -D vitest @vitest/ui
npm install -D @testing-library/react @testing-library/jest-dom
npm install -D @testing-library/user-event
npm install -D msw
npm install -D @playwright/test
npm install -D happy-dom # or jsdom React App
- [ ] Create `apps/react-ui/` directory
- [ ] Initialize with Vite + React + TypeScript
- [ ] Configure ESLint, Prettier, TypeScript strict mode
- [ ] Setup pre-commit hooks (already exist at repo level)

#### 1.2 Install Dependencies - 🔄 PARTIALLY COMPLETED

**✅ INSTALLED:**
```bash
# Core - DONE
npm install react react-dom react-router-dom
npm install bootstrap react-bootstrap bootstrap-icons
npm install @tanstack/react-query axios

# Query Builder - DONE (but custom implementation, not using library features)
npm install react-querybuilder

# Charts & Visualization - DONE
npm install recharts react-cytoscapejs cytoscape

# Utilities
npm install date-fns clsx

# PWA
npm install workbox-precaching workbox-routing

# Dev Dependencies
npm install -D @types/react @types/react-dom
npm install -D @typescript-eslint/eslint-plugin @typescript-eslint/parser
npm install -D sass
npm install -D vite-plugin-pwa
```

#### 1.3 Configure Build System - ✅ COMPLETED

- [x] Update `vite.config.ts` with aliases, proxy to API
- [x] Configure Bootstrap SCSS imports
- [x] Setup environment variables (API base URL)
- [x] Configure PWA with vite-plugin-pwa
- [x] Static assets (logo, favicon) serving correctly
- [x] Multi-stage Dockerfile (Node build + nginx serve)

#### 1.4 Create Base Layout & Branding - ✅ COMPLETED

- [x] `AppLayout.tsx` - Main layout container
- [x] `Sidebar.tsx` - Navigation sidebar with ollyScale logo
- [x] `Header.tsx` - Top header with breadcrumbs
- [x] Routing setup with React Router
- [x] `LoadingSpinner.tsx` - Animated logo spinner
- [x] `EmptyState.tsx` - Logo-based empty states

### Phase 2: API Client & State Management (Week 1-2) - ✅ COMPLETED

#### 2.1 API Client - ✅ COMPLETED

- [x] Create `api/client.ts` with axios instance
- [x] Implement API types from OpenAPI spec (in `api/types/`)
- [x] Enhanced error handling and response transformation with APIError type
- [x] Request/response interceptors with user-friendly error messages
- [x] Status code-specific error handling (400, 401, 403, 404, 422, 429, 500, 503)
- [x] Network error and timeout handling
- [x] Development-only error logging

#### 2.2 React Query Setup - ✅ COMPLETED

- [x] Configure QueryClient with defaults
- [x] Create base query hooks:
  - [x] `useTracesQuery` (POST /api/traces/search)
  - [x] `useSpansQuery` (POST /api/spans/search)
  - [x] `useLogsQuery` (POST /api/logs/search)
  - [x] `useMetricsQuery` (POST /api/metrics/search)
  - [x] `useServicesQuery` (POST /api/services)
  - [x] `useServiceMapQuery` (POST /api/service-map)
  - [x] `useTraceDetailQuery` (GET /api/traces/{id})

#### 2.3 Context Providers - ✅ COMPLETED

- [x] ThemeContext (dark/light/auto mode with system preference detection)
- [x] QueryContext (filters, time ranges, live mode, presets)
- [x] RefreshContext (auto-refresh toggle + interval)
- [x] DocsContext - DEFERRED (embedded docs not needed yet)

#### 2.4 Custom Hooks - ✅ COMPLETED

- [x] `useAutoRefresh` - Auto-refresh logic with RefreshContext integration and sliding time window
- [x] `useQuery` - Re-export of QueryContext hook
- [x] `useDebounce` - Debounce values for search inputs (500ms default)
- [x] `useLocalStorage` - Type-safe localStorage persistence with cross-tab sync
- [x] `usePagination` - DEFERRED (API handles pagination internally)

### Phase 3: Query Builder Component (Week 2) - ⚠️ CUSTOM IMPLEMENTATION (NOT USING LIBRARY)

**STATUS**: Custom implementation built, react-querybuilder installed but NOT used
**DECISION NEEDED**: Refactor to use library OR remove dependency

#### 3.1 Query Builder Core - ✅ CUSTOM IMPLEMENTATION

- [x] Custom QueryBuilder components (QueryBuilder.tsx, CompactQueryBuilder.tsx, EnhancedQueryBuilder.tsx)
- [x] OTLP field schemas defined for traces, spans, logs, metrics
- [ ] NOT using `react-querybuilder` library features (❌ TECHNICAL DEBT)
- [x] Field schemas in FieldSchema interface

#### 3.2 Custom Operators - ✅ IMPLEMENTED

- [x] Operators: `eq`, `ne`, `gt`, `lt`, `gte`, `lte`, `contains`, `regex`
- [x] Type-specific value inputs (string, number, enum, boolean)
- [x] Enum dropdowns for fields like span.kind, severity_text
- [x] DateTimePicker for custom time ranges

#### 3.3 Filter Presets - ✅ IMPLEMENTED

- [x] Save/load presets to localStorage via QueryContext
- [x] Time range quick filters (5m, 15m, 30m, 1h, 3h, 6h, 12h, 24h)
- [x] Delete presets functionality
- [x] Preset modal for saving with name/description

#### 3.4 Query Builder UI - ✅ IMPLEMENTED

- [x] Bootstrap styling throughout
- [x] Add/remove individual filters
- [ ] NO filter groups (AND/OR logic) - only flat filter list
- [ ] NO field autocomplete
- [x] Basic validation (empty field warnings)

### Phase 4: Core Pages - Traces & Spans (Week 3) - ✅ COMPLETED

#### 4.1 Traces Page - ✅ COMPLETED

- [x] `TracesPage.tsx` - Traces table with filters
- [x] Table-based UI (no separate TraceList/TraceCard components - simpler approach)
- [x] Query builder integration (EnhancedQueryBuilder)
- [x] Status code filter buttons - DEFERRED (can filter via query builder)
- [x] Export JSON functionality (DownloadButton component)

#### 4.2 Trace Detail View - ✅ COMPLETED

- [x] Waterfall shown in modal (no separate TraceDetail.tsx needed)
- [x] `TraceWaterfall.tsx` - Span timeline visualization with duration bars
- [x] `SpanDetail.tsx` - Span detail modal with attributes
- [x] `CorrelatedLogs.tsx` - Logs linked to trace/span IDs
- [x] Navigation: trace → spans → logs (clickable IDs throughout)

#### 4.3 Spans Page - ✅ IMPLEMENTED

- [x] `SpansPage.tsx` - Spans table with filters
- [x] Service filtering via query builder
- [x] Query builder for span attributes
- [x] Link to parent trace (clickable trace IDs)

### Phase 5: Logs & Metrics Pages (Week 3-4) - ✅ COMPLETED

#### 5.1 Logs Page - ✅ COMPLETED

- [x] `LogsPage.tsx` - Logs list with expandable rows
- [x] Table-based UI (no separate LogCard component - simpler approach)
- [x] Trace correlation links (clickable trace IDs)
- [x] Severity filtering (ERROR, WARN, INFO, DEBUG) via query builder
- [x] Log body rendering with attribute fallback
- [x] **UX Improvements:**
  - [x] Empty body detection (null, undefined, "", "{}")
  - [x] Attribute fallback for empty bodies (shows first 2-3 attributes)
  - [x] Column renamed from "Message" to "Event Data"
  - [x] Expandable row details with full attributes and body
- [x] **Deferred Features:**
  - Log streaming/tailing mode (live mode with auto-refresh provides similar UX)
  - Custom log level badge colors (Bootstrap badges sufficient)

#### 5.2 Metrics Page - ✅ COMPLETED

- [x] `MetricsPage.tsx` - Metrics list with dense table layout
- [x] Metric overview with cardinality column
- [x] Metric detail modal with time-series chart
- [x] Cardinality explorer modal:
  - [x] Label analysis with expandable attribute values
  - [x] High-cardinality warnings (visual indicators)
  - [x] Series count display
  - [x] Raw series view (PromQL format)
  - [x] Export functionality (Copy PromQL, Download JSON)
- [x] RED metrics display
- [x] **Deferred Features:**
  - Recharts improvements (current Chart.js integration works well)
  - Metric type filtering (can filter via query builder)
  - Time aggregation (handled by backend)

### Phase 6: Services & Service Map (Week 4) - ✅ COMPLETED

#### 6.1 Service Catalog - ✅ COMPLETED

- [x] `ServiceCatalogPage.tsx` - Service list with RED metrics
- [x] Service cards with metrics display
- [x] Sortable table with inline charts
- [x] Inline metric charts (simplified view)
- [x] Navigate to service traces/spans via query builder

#### 6.2 Service Map - ✅ COMPLETED

- [x] `ServiceMapPage.tsx` - Interactive service map page
- [x] `ServiceGraph.tsx` - React Cytoscape component
- [x] React Cytoscape integration
- [x] Interactive graph (zoom, pan, drag)
- [x] Zoom controls (in/out/fit/center)
- [x] Node types with color coding (Client, Server, Database, Messaging, External)
- [x] Edge labels showing call counts
- [x] Edge thickness based on traffic volume
- [x] Node selection with metrics popup
- [x] Layout switching (hierarchical/grid)
- [x] Real-time updates via auto-refresh
- [x] Node click shows service metrics (requests, errors, P50 latency)
- [x] **NEW**: OTEL semantic conventions for icon detection (db.system, messaging.system)
- [x] **NEW**: Local devicon fonts with Unicode characters (no CDN dependency)
- [x] **NEW**: Theme-compatible colors for light/dark mode
- [x] **NEW**: Removed borders, improved visual styling
- [x] **NEW**: PostgreSQL, MySQL, MongoDB, Redis, Kafka, RabbitMQ, Nginx icons

### Phase 7: UI Polish & Optimization (Future/Optional) - ⏸️ DEFERRED

#### 7.1 Query Builder Space Optimization

**Status**: Deferred - Not critical for MVP
**Goal**: Reduce vertical space usage of EnhancedQueryBuilder component (~50% reduction target)
**Current State**: Fully functional with all features (time range, filters, presets)

Optimization tasks:

- [ ] Compact time range section (horizontal layout, smaller buttons)
- [ ] Reduce form control padding (use size="sm" consistently)
- [ ] Collapse advanced filters by default with toggle
- [ ] Reduce card padding (py-3 → py-2)
- [ ] Make preset UI more compact (dropdown or smaller buttons)
- [ ] Consider collapsible sections for less-used features

**Important**: Do NOT remove functionality during optimization. All features must remain:

- ✅ Time range presets and custom date/time selection
- ✅ Namespace and service filtering
- ✅ Free text search
- ✅ Advanced filters with add/remove
- ✅ Saved presets with delete capability
- ✅ Query reset and builder collapse

### Phase 8: AI Agents & Collector Config & Embedded Docs (Week 5) - 🔄 PARTIALLY STARTED

#### 8.1 AI Agents Page - 🔄 BASIC PAGE EXISTS

- [x] `AIAgentsPage.tsx` - Basic page structure created
- [ ] LLM session list view - NOT IMPLEMENTED
- [ ] GenAI span visualization - NOT IMPLEMENTED
- [ ] Token tracking (input/output) - NOT IMPLEMENTED
- [ ] Cost estimation - NOT IMPLEMENTED
- [ ] Prompt/response viewer - NOT IMPLEMENTED
- [ ] Model filtering - NOT IMPLEMENTED

#### 8.2 OTel Collector Config Page - 🔄 BASIC PAGE EXISTS

- [x] `OtelConfigPage.tsx` - Basic page structure created
- [ ] OpAMP status display - NOT IMPLEMENTED
- [ ] Configuration viewer - NOT IMPLEMENTED
- [ ] Validation feedback - NOT IMPLEMENTED
- [ ] Apply changes UI - NOT IMPLEMENTED
- [ ] Collector templates - NOT IMPLEMENTED

#### 8.3 Embedded Documentation - ❌ NOT STARTED

##### 8.3.1 Documentation Structure

- [ ] Convert existing docs to React components
- [ ] Markdown rendering with `react-markdown`
- [ ] Code syntax highlighting
- [ ] In-app navigation
- [ ] Search functionality

##### 8.3.2 Context-Sensitive Help

- [ ] "?" icon on each page
- [ ] Popover with relevant docs
- [ ] Keyboard shortcuts (Ctrl+/)
- [ ] Tooltips on complex features

##### 8.3.3 Documentation Pages

- [ ] Quick Start guide
- [ ] Traces documentation
- [ ] Logs documentation
- [ ] Metrics documentation
- [ ] Query builder guide
- [ ] API reference (embedded OpenAPI)
- [ ] Troubleshooting

#### 10.1 OpenTelemetry Browser Setup

- [ ] Configure OpenTelemetry SDK in `telemetry.ts`
- [ ] Auto-instrumentation for:
  - Page loads and navigation
  - User interactions (clicks, form submissions)
  - Fetch/XHR API calls
  - Phase 12: Performance & Polish (Week 9)

#### 12.1 Performance Optimization

- [ ] React.memo for expensive components
- [ ] Virtualization for large lists (react-window or TanStack Virtual)
- [ ] Query caching strategy with React Query
- [ ] Code splitting with React.lazy
- [ ] Bundle size optimization (tree-shaking, compression)
- [ ] Image optimization (lazy loading, WebP)
- [ ] Web Vitals monitoring with OpenTelemetry

#### 12.2 Accessibility

- [ ] Keyboard navigation (tab order, shortcuts)
- [ ] ARIA labels and roles
- [ ] Focus management (modals, drawers)
- [ ] Screen reader support
- [ ] Color contrast (WCAG AA)
- [ ] Reduced motion support
- [ ] Skip to main content link

#### 12.3 Polish

- [ ] Loading states (skeletons, spinners)
- [ ] 3.1 OpenTelemetry Collector for Browser Telemetry
- [ ] Create dedicated OTel Collector instance for UI telemetry
- [ ] Collector configuration:
  - OTLP HTTP receiver on `/v1/traces`, `/v1/metrics`, `/v1/logs`
  - Batch processor
  - Forward to main OTLP receiver
  - CORS headers for browser access
- [ ] Deploy as separate service: `ollyscale-ui-collector`
- [ ] Helm chart updates:
  - Add `uiCollector` section to `values.yaml`
  - Deployment manifest for UI collector
  - Service manifest (ClusterIP)
  - HTTPRoute for `/api/v1/otlp/*` (browser access)

#### 13.2 Kubernetes HTTPRoute for Browser Telemetry

- [ ] Create HTTPRoute in Helm chart:

  ```yaml
  apiVersion: gateway.networking.k8s.io/v1
  kind: HTTPRoute
  metadata:
    name: ollyscale-ui-telemetry
    namespace: ollyscale
  spec:
    parentRefs:
      - name: ollyscale-gateway
        namespace: ollyscale
    hostnames:
      - "ollyscale.test"
    rules:
      - matches:
          - path:
              type: PathPrefix
              value: /api/v1/otlp
        backendRefs:
          # OTel Operator creates service with format: {name}-collector
          - name: ollyscale-ui-collector-collector
            port: 4318
        filters:
          - type: ResponseHeaderModifier
            responseHeaderModifier:
              add:
                - name: Access-Control-Allow-Origin
                  value: "https://ollyscale.test"
                - name: Access-Control-Allow-Methods
                  value: "POST, OPTIONS"
                - name: Access-Control-Allow-Headers
                  value: "Content-Type, Authorization"
  ```

- [ ] CORS already handled by collector config (belt-and-suspenders approach)
- [ ] Rate limiting handled by collector's `memory_limiter` processor

#### 13.3 Docker Build

- [ ] Update `Dockerfile` for React build
- [ ] Multi-stage build:
  1. Build stage: Node.js + npm build
  2. Runtime stage: nginx + static files
- [ ] Environment variable injection at runtime (not build time)
- [ ] Health check endpoint
- [ ] Non-root user

#### 13.4 Helm Chart Updates

- [ ] Update `charts/ollyscale/` to use new UI image
- [ ] Add UI collector deployment and service
- [ ] Add HTTPRoute for UI telemetry
- [ ] ConfigMap for nginx configuration
- [ ] ConfigMap for i18n translations (if external)
- [ ] Update image references in `values.yaml`

#### 13.5 Documentation Update

- [ ] Update README with new UI screenshots
- [ ] Document query builder usage
- [ ] Document i18n/localization
- [ ] Document browser telemetry setup
- [ ] Migration guide from old UI
- [ ] Architecture diagrams (Mermaid)

#### 13.6 CI/CD Pipeline Updates

- [ ] Update `.github/workflows/` for React app:
  - Build workflow (npm build, TypeScript check)
  - Test workflow (Vitest unit, RTL component, Playwright E2E)
  - Lint workflow (ESLint, Prettier)
  - Docker build workflow (multi-arch: amd64, arm64)
  - Release workflow (version bump, changelog, publish images)
- [ ] Add workflow for dependency updates (Renovate/Dependabot)
- [ ] Add workflow for bundle size monitoring
- [ ] Add workflow for accessibility testing (axe-core)
- [ ] Add workflow for lighthouse CI (performance)

#### 13.7 Performance Budgets & Monitoring

- [ ] Define performance budgets:
  - Initial bundle size: < 500 KB gzipped
  - Time to Interactive (TTI): < 3s on 3G
  - First Contentful Paint (FCP): < 1.5s
  - Largest Contentful Paint (LCP): < 2.5s
  - Cumulative Layout Shift (CLS): < 0.1
- [ ] Add bundle analyzer (rollup-plugin-visualizer)
- [ ] Add performance monitoring with Web Vitals
- [ ] Set up alerts for performance regressions

#### 13.8 Migration Strategy

- [ ] **Phase 1**: Deploy new UI at `/beta` path (parallel to old UI)
- [ ] **Phase 2**: Beta testing with selected users (2 weeks)
- [ ] **Phase 3**: Add feature flag to switch between UIs
- [ ] **Phase 4**: Make new UI default (old UI at `/legacy`)
- [ ] **Phase 5**: Deprecation notice for old UI (4 weeks)
- [ ] **Phase 6**: Remove old UI completely
- [ ] Document migration process for users
- [ ] Provide feedback mechanism during beta
- [ ] Track adoption metrics (which UI users choose)

#### 13.9 Cleanup

- [ ] Remove `apps/ollyscale-ui/` (old UI) - **ONLY AFTER Phase 6**
- [ ] Update build scripts in `scripts/build/`
- [ ] Update CI/CD pipelines (.github/workflows)
- [ ] Remove TinyOlly legacy code references
- [ ] Update `release-please-config.json`
- [ ] Archive old UI documentation, OTLP helpers
- [ ] Test API client: request/response handling, errors
- [ ] Test contexts: theme, namespace, refresh, language
- [ ] Coverage target: 80%+

#### 11.2 Component Tests (React Testing Library)

- [ ] Test common components: buttons, badges, cards, modals
- [ ] Test query builder: filter add/remove, operators, validation
- [ ] Test telemetry cards: TraceCard, SpanCard, LogCard, MetricCard
- [ ] Test pages: rendering, loading states, error states
- [ ] User interaction tests with `@testing-library/user-event`
- [ ] Accessibility tests (keyboard nav, ARIA)

#### 11.3 Integration Tests (MSW)

- [ ] Mock API endpoints with MSW
- [ ] Test complete user flows:
  - Search traces → view detail → see logs
  - Apply filters → see results
  - Auto-refresh → data updates
  - Change language → UI updates
- [ ] Test error scenarios: 404, 500, network errors
- [ ] Test pagination and infinite scroll

#### 11.4 E2E Tests (Playwright)

- [ ] Critical user paths:
  - Navigate tabs
  - Apply query builder filters
  - View trace waterfall
  - Check service map
  - Change theme/language
- [ ] Cross-browser testing (Chrome, Firefox, Safari)
- [ ] Visual regression tests (screenshots)
- [ ] Performance tests (Lighthouse

### Phase 8: AI Agents & Collector Config & Embedded Docs (Week 5) - 🔄 PARTIALLY STARTED

#### 8.1 AI Agents Page - 🔄 BASIC PAGE EXISTS

- [x] `AIAgentsPage.tsx` - Basic page structure created
- [ ] LLM session list view - NOT IMPLEMENTED
- [ ] GenAI span visualization - NOT IMPLEMENTED
- [ ] Token tracking (input/output) - NOT IMPLEMENTED
- [ ] Cost estimation - NOT IMPLEMENTED
- [ ] Prompt/response viewer - NOT IMPLEMENTED
- [ ] Model filtering - NOT IMPLEMENTED

#### 8.2 OTel Collector Config Page - 🔄 BASIC PAGE EXISTS

- [x] `OtelConfigPage.tsx` - Basic page structure created
- [ ] OpAMP status display - NOT IMPLEMENTED
- [ ] Configuration viewer - NOT IMPLEMENTED
- [ ] Validation feedback - NOT IMPLEMENTED
- [ ] Apply changes UI - NOT IMPLEMENTED
- [ ] Collector templates - NOT IMPLEMENTED

#### 8.3 Embedded Documentation - ❌ NOT STARTED

##### 8.3.1 Documentation Structure

- [ ] Convert existing docs to React components
- [ ] Markdown rendering with `react-markdown`
- [ ] Code syntax highlighting
- [ ] In-app navigation
- [ ] Search functionality

##### 8.3.2 Context-Sensitive Help

- [ ] "?" icon on each page
- [ ] Popover with relevant docs
- [ ] Keyboard shortcuts (Ctrl+/)
- [ ] Tooltips on complex features

##### 8.3.3 Documentation Pages

- [ ] Quick Start guide
- [ ] Traces documentation
- [ ] Logs documentation
- [ ] Metrics documentation
- [ ] Query builder guide
- [ ] API reference (embedded OpenAPI)
- [ ] Troubleshooting

### Phase 9: Auto-Refresh & Controls (Week 6) - ✅ COMPLETED

#### 9.1 Auto-Refresh Logic - ✅ COMPLETED

- [x] `useAutoRefresh` hook - Implemented in [apps/web-ui/src/hooks/useAutoRefresh.ts](../apps/web-ui/src/hooks/useAutoRefresh.ts)
- [x] Toggle button in EnhancedQueryBuilder - LIVE/PAUSED button with icons
- [x] Configurable interval (5s default) - Hardcoded to 5s in useAutoRefresh hook
- [x] **Sliding time window** - When LIVE mode enabled, time range updates on each refresh
- [x] Auto-disable live mode when user manually adjusts time - Prevents unexpected behavior
- [x] LocalStorage persistence - Live mode state persists across page reloads

#### 9.2 Global Controls - ✅ PARTIALLY COMPLETED

- [x] Time range selector (last N minutes) - 5/15/30/60 minute buttons with LIVE mode integration
- [x] Time range presets highlight when active - Visual feedback for selected relative window
- [x] Timezone display on all timestamps - Shows "UTC" or local timezone abbreviation
- [x] Manual time range picker - DateTimePicker for custom start/end selection
- [ ] Namespace filter dropdown (multi-select) - Exists but not multi-select
- [ ] Theme toggle (dark/light) - Not yet implemented
- [ ] Refresh button (manual) - Exists in query builder (via refetch)

### Phase 10: Testing & i18n (Week 7) - 🔄 PARTIALLY STARTED

#### 10.1 Testing Infrastructure - ✅ SETUP COMPLETE, 🔄 TESTS NEEDED

**Status**: Testing libraries installed, vitest configured, 1 test file exists (useDebounce.test.ts)

**✅ Completed**:

- [x] Install Vitest@4.0.18, @vitest/ui
- [x] Install React Testing Library (@testing-library/react@16.3.2, jest-dom@6.9.1, user-event@14.6.1)
- [x] Configure vitest.config.ts
- [x] Add test scripts to package.json (test, test:watch, test:coverage, test:ui)
- [x] First test written: useDebounce.test.ts (4 test cases)

**🔄 Tests Needed** (⏱️ 3-4 days for comprehensive coverage):

- [ ] Install <MSW@2.x> for API mocking (not yet installed)
- [ ] Create test setup file (src/test/setup.ts)
- [ ] Unit tests for hooks: useAutoRefresh, useLocalStorage, useTracing, useQuery
- [ ] Unit tests for utilities: dateUtils, formatters, validators
- [ ] Component tests with React Testing Library:
  - [ ] Common components (buttons, badges, cards, modals)
  - [ ] Query builder components
  - [ ] Page components (rendering, loading, error states)
- [ ] API client tests with MSW
- [ ] Context tests (ThemeContext, QueryContext, RefreshContext)
- [ ] E2E tests with Playwright (optional)

**Coverage Goal**: 80%+ code coverage

#### 10.2 Browser Telemetry - ✅ COMPLETE (Basic), 🔄 ENHANCEMENTS NEEDED

**Status**: Core implementation complete with automatic traces, needs error handling enhancements

**✅ Completed** (2026-01-30):

- [x] Install @opentelemetry/api, sdk-trace-web
- [x] Install auto-instrumentation packages (auto-instrumentations-web meta-package)
- [x] Install OTLP exporter (exporter-trace-otlp-http)
- [x] Create src/telemetry/ configuration files:
  - [x] config.ts - Provider, exporter, consent checking
  - [x] instrumentations.ts - Auto-instrumentations for document-load, user-interaction, fetch, XHR
- [x] GDPR consent banner component (ConsentBanner.tsx)
- [x] Telemetry opt-in/opt-out mechanism (localStorage-based)
- [x] OpenTelemetryCollector CR deployed (ollyscale-browser-collector)
- [x] HTTPRoute configured for /v1/traces with CORS
- [x] useTracing hook with startSpan, recordError, addEvent helpers

**Browser Telemetry Captures** (Auto-instrumented):

- ✅ Page load performance metrics (document-load instrumentation)
- ✅ User interactions (clicks, form submits, keypresses)
- ✅ API call tracing with trace propagation (fetch/XHR)
- ✅ Resource attributes (service.name: ollyscale-web-ui, service.version, deployment.environment)

**🔄 Needed Enhancements** (⏱️ 1 day):

- [ ] Global error handler for unhandled exceptions (`window.onerror`)
- [ ] Global promise rejection handler (`window.onunhandledrejection`)
- [ ] ErrorBoundary component to catch React errors
- [ ] Custom events for business logic (button clicks, filter changes, etc.)
- [ ] Error sampling strategy (100% errors, 10% success)

#### 10.3 Internationalization - ✅ COMPLETE (2026-02-01)

**Status**: Fully implemented with 287 translation keys across 16 namespaces

- [x] Install react-i18next, i18next, i18next-browser-languagedetector
- [x] Create src/i18n/config.ts configuration with LanguageDetector
- [x] Create src/i18n/locales/en-US/translation.json (287 keys)
- [x] Create src/i18n/locales/en-GB/translation.json (UK spelling variants)
- [x] Import i18n config in main.tsx before App render
- [x] Replace hardcoded strings with t() function (all pages, sidebar, common components)
- [x] LanguageSelector component with flag dropdowns (🇺🇸/🇬🇧)
- [x] Language persistence via localStorage
- [x] Date format localization (US: MM/DD/YYYY vs GB: DD/MM/YYYY)

**Translation Namespaces**: app, nav, sidebar, common, query, dashboard, traces, spans, logs, metrics, services, serviceMap, aiAgents, otelConfig, consent, theme, errors, dateTime

**Commit**: 1a166f2 - feat(web-ui): implement internationalization (i18n) support

#### 10.4 Performance Optimization - 🔄 BASIC IMPLEMENTATION

- [x] Basic React Query caching (enabled by default)
- [ ] React.memo for expensive components
- [ ] Virtualization for large lists (react-window)
- [ ] Code splitting with React.lazy
- [ ] Bundle size optimization

#### 10.5 Accessibility - ❌ NOT STARTED

- [ ] Keyboard navigation
- [ ] ARIA labels
- [ ] Focus management
- [ ] Screen reader support
- [ ] Color contrast audit (WCAG AA)
- [ ] Reduced motion support

#### 10.6 PWA & Polish - 🔄 PARTIALLY IMPLEMENTED

- [x] vite-plugin-pwa installed
- [ ] PWA manifest configuration
- [ ] Service worker registration
- [ ] App icons (192x192, 512x512)
- [ ] Install prompt testing
- [x] LoadingSpinner component exists
- [x] EmptyState component exists
- [ ] Error states with ErrorBoundary
- [ ] Animations/transitions
- [x] Responsive design (mobile-friendly)

#### 10.7 GDPR Compliance - ❌ NOT STARTED

- [ ] ConsentBanner.tsx component
- [ ] Telemetry opt-in/opt-out UI
- [ ] Store consent in localStorage
- [ ] Respect consent in telemetry init
- [ ] Privacy policy link in footer

### Phase 11: Infrastructure & Deployment (Week 8) - 🔄 PARTIALLY COMPLETE

#### 11.1 Docker Build - ✅ COMPLETED

- [x] Multi-stage Dockerfile (Node build + nginx serve)
- [x] Non-root user
- [x] Static assets copied correctly
- [ ] Environment variable injection at runtime (currently build-time)
- [x] Health check endpoint (nginx default)

#### 11.2 Helm Chart - ✅ DEPLOYED

- [x] `charts/ollyscale/` exists and deployed
- [x] web-ui deployment configured
- [x] HTTPRoute for web UI
- [x] Service created
- [x] Image references in values.yaml
- [ ] OpenTelemetryCollector CR for UI telemetry - NOT CREATED
- [ ] HTTPRoute for /api/v1/otlp/* - NOT CREATED
- [ ] ConfigMap for i18n translations - NOT NEEDED YET

#### 11.3 CI/CD Pipeline Updates - ❌ NOT STARTED

- [ ] Test workflow (Vitest unit, RTL component, Playwright E2E)
- [ ] Lint workflow improvements
- [ ] Bundle size monitoring
- [ ] Accessibility testing (axe-core)
- [ ] Lighthouse CI
- [x] Docker build workflow exists (builds on push)

#### 11.4 Documentation Updates - 🔄 PARTIALLY DONE

- [ ] Update README with new UI screenshots
- [ ] Document query builder usage
- [ ] Document i18n/localization (when implemented)
- [ ] Document browser telemetry setup (when implemented)
- [ ] Migration guide from old UI
- [x] Implementation plan exists
- [x] Status report created

#### 11.5 Migration Strategy - ❌ NOT PLANNED YET

- [ ] Decide: parallel deployment or full switch
- [ ] If parallel: HTTPRoute configuration for /beta path
- [ ] Beta testing period duration
- [ ] Rollback plan
- [ ] Old UI removal timeline

## Query Builder Design

### Filter Structure

```typescript
interface Filter {
  field: string;      // e.g., "service.name", "http.status_code"
  operator: string;   // eq, ne, gt, lt, gte, lte, contains, regex
  value: any;         // string, number, boolean, etc.
}

interface FilterGroup {
  combinator: 'AND' | 'OR';
  filters: (Filter | FilterGroup)[];
}
```

### Example Query Builder UI

```
┌─────────────────────────────────────────────────────────────┐
│ Query Builder                                    [Save] [Clear]│
├─────────────────────────────────────────────────────────────┤
│ [AND ▼]                                                      │
│   ┌─────────────────────────────────────────────────────┐  │
│   │ service.name    [equals ▼]  demo-frontend    [-]    │  │
│   └─────────────────────────────────────────────────────┘  │
│   ┌─────────────────────────────────────────────────────┐  │
│   │ http.status_code [gte ▼]    400                [-]   │  │
│   └─────────────────────────────────────────────────────┘  │
│   [+ Add Filter]                                           │
│                                                              │
│ [Apply Filter]                                               │
└──────────────────────────────────────────────────────────────┘
```

### OTLP Field Schema

#### Trace/Span Fields

- `trace_id` (string)
- `span_id` (string)
- `service.name` (string)
- `service.namespace` (string)
- `span.kind` (enum: INTERNAL, SERVER, CLIENT, PRODUCER, CONSUMER)
- `http.method` (enum: GET, POST, PUT, DELETE, PATCH)
- `http.status_code` (number)
- `http.route` (string)
- `duration_seconds` (number)
- `status.code` (enum: UNSET, OK, ERROR)

#### Log Fields

- `severity_text` (enum: DEBUG, INFO, WARN, ERROR, FATAL)
- `severity_number` (number: 0-24)
- `body` (string or structured)
- `trace_id` (string)
- `span_id` (string)

#### Metric Fields

- `metric.name` (string)
- `metric.type` (enum: Gauge, Counter, Histogram, Summary)
- `attributes.*` (dynaBrowser telemetry + i18n + themes |
| Phase 11 | 1 week | Testing & quality |
| Phase 12 | 1 week | Performance & polish |
| Phase 13 | 0.5 weeks | Infrastructure & deployment |
| **Total** | **13 Customization

### Color Palette

```scss
// apps/react-ui/src/styles/variables.scss

// Primary colors
$primary: #0d6efd;
$secondary: #6c757d;
$success: #198754;
$danger: #dc3545;
$warning: #ffc107;
$info: #0dcaf0;

// Dark theme
$dark-bg: #1a1a1a;
$dark-surface: #2d2d2d;
$dark-border: #404040;
$dark-text: #e0e0e0;

// Light theme
$light-bg: #ffffff;
$light-surface: #f8f9fa;
$light-border: #dee2e6;
$light-text: #212529;

// Trace status colors
$status-ok: #10b981;
$status-error: #ef4444;
$status-unset: #6b7280;
```

Browser Telemetry Architecture

### OpenTelemetry Collector for UI Telemetry

```
Browser (React App)
  │
  │ OTLP/HTTP (fetch)
  │ /api/v1/otlp/v1/traces
  │ /api/v1/otlp/v1/metrics
  │
  ↓
Envoy Gateway (HTTPRoute)
  │
  ↓
ollyscale-ui-collector:4318 (OTLP HTTP)
  │
  │ processors: batch, resource
  │
  ↓
ollyscale-otlp-receiver:4343 (main ingestion)
  │
  ↓
Redis Storage
```

### Telemetry Configuration (`telemetry.ts`)

```typescript
import { WebTracerProvider } from '@opentelemetry/sdk-trace-web';
import { Resource } from '@opentelemetry/resources';
import { SEMRESATTRS_SERVICE_NAME, SEMRESATTRS_SERVICE_VERSION, SEMRESATTRS_SERVICE_NAMESPACE } from '@opentelemetry/semantic-conventions';
import { OTLPTraceExporter } from '@opentelemetry/exporter-trace-otlp-http';
import { BatchSpanProcessor } from '@opentelemetry/sdk-trace-base';
import { registerInstrumentations } from '@opentelemetry/instrumentation';
import { DocumentLoadInstrumentation } from '@opentelemetry/instrumentation-document-load';
import { UserInteractionInstrumentation } from '@opentelemetry/instrumentation-user-interaction';
import { FetchInstrumentation } from '@opentelemetry/instrumentation-fetch';
import { XMLHttpRequestInstrumentation } from '@opentelemetry/instrumentation-xml-http-request';
import { ZoneContextManager } from '@opentelemetry/context-zone';

export function initTelemetry() {
  // Check if user has consented (GDPR compliance)
  const telemetryEnabled = localStorage.getItem('ollyscale-telemetry-consent') !== 'false';
  if (!telemetryEnabled) {
    console.info('Browser telemetry disabled by user preference');
    return;
  }

  const provider = new WebTracerProvider({
    resource: new Resource({
      [SEMRESATTRS_SERVICE_NAME]: 'ollyscale-ui',
      [SEMRESATTRS_SERVICE_VERSION]: import.meta.env.VITE_APP_VERSION || 'dev',
      [SEMRESATTRS_SERVICE_NAMESPACE]: 'ollyscale',
      'deployment.environment': import.meta.env.MODE || 'production',
    }),
  });

  // Export to dedicated UI collector via Gateway HTTPRoute
  const exporter = new OTLPTraceExporter({
    url: '/api/v1/otlp/v1/traces',
    headers: {
      // Could add auth token here if needed
    },
  });

  provider.addSpanProcessor(new BatchSpanProcessor(exporter, {
    maxQueueSize: 100,
    maxExportBatchSize: 10,
    scheduledDelayMillis: 5000,
  }));

  // Use ZoneContextManager for better async context propagation
  provider.register({
    contextManager: new ZoneContextManager(),
  });

  // Auto-instrumentation
  registerInstrumentations({
    instrumentations: [
      new DocumentLoadInstrumentation(),
      new UserInteractionInstrumentation({
        eventNames: ['click', 'submit'],
        shouldPreventSpanCreation: (eventType, element, span) => {
          // Don't create spans for auto-refresh background activity
          if (element.id === 'auto-refresh-btn') return true;
          return false;
        },
      }),
      new FetchInstrumentation({
        propagateTraceHeaderCorsUrls: [/.*/],
        clearTimingResources: true,
        ignoreUrls: [/api\/v1\/otlp/], // Don't trace telemetry exports
        applyCustomAttributesOnSpan: (span, request, result) => {
          // Add custom attributes for API calls
          if (request.url.includes('/api/')) {
            span.setAttribute('http.url', request.url);
            if (result instanceof Response) {
              span.setAttribute('http.status_code', result.status);
            }
          }
        },
      }),
      new XMLHttpRequestInstrumentation({
        propagateTraceHeaderCorsUrls: [/.*/],
        ignoreUrls: [/api\/v1\/otlp/],
      }),
    ],
  });

  console.info('OpenTelemetry browser instrumentation initialized');
}

// Call from main.tsx after user consent check
```

### Captured Browser Telemetry

1. **Page Load Spans**
   - DNS lookup time
   - Connection time
   - Request/response time
   - DOM interactive, complete
   - First paint, contentful paint

2. **Navigation Spans**
   - Route changes (React Router)
   - Component mount/unmount

3. **User Interaction Spans**
   - Button clicks
   - Form submissions
   - Query builder interactions

4. **API Call Spans**
   - Fetch requests to `/api/*`
   - Request/response times
   - Status codes, errors

5. **Error Spans**
   - JavaScript errors
   - React error boundaries
   - API errors

## Internationalization (i18n) Implementation

### Translation File Structure

```json
// locales/en-US/translation.json (US English)
{
  "nav": {
    "traces": "Traces",
    "logs": "Logs",
    "metrics": "Metrics",
    "serviceMap": "Service Map",
    "serviceCatalog": "Service Catalog",
    "aiAgents": "AI Agents",
    "collectorConfig": "OTel Config",
    "docs": "Documentation"
  },
  "actions": {
    "search": "Search",
    "filter": "Filter",
    "clear": "Clear",
    "apply": "Apply",
    "export": "Export",
    "copy": "Copy",
    "download": "Download",
    "refresh": "Refresh"
  },
  "queryBuilder": {
    "addFilter": "Add Filter",
    "addGroup": "Add Group",
    "field": "Field",
    "operator": "Operator",
    "value": "Value",
    "operators": {
      "eq": "Equals",
      "ne": "Not Equals",
      "gt": "Greater Than",
      "lt": "Less Than",
      "gte": "Greater Than or Equal",
      "lte": "Less Than or Equal",
      "contains": "Contains",
      "regex": "Regex Match"
    }
  },
  "telemetry": {
    "traces": {
      "title": "Traces",
      "traceId": "Trace ID",
      "duration": "Duration",
      "spans": "Spans",
      "status": "Status"
    }
  }
}
```

### Usage in Components

```typescript
import { useTranslation } from 'react-i18next';

export function TracesPage() {
  const { t } = useTranslation();

  return (
    <div>
      <h1>{t('telemetry.traces.title')}</h1>
      <button>{t('actions.refresh')}</button>
    </div>
  );
}
```

### Language Selector

```typescript
import { useTranslation } from 'react-i18next';

export function LanguageSelector() {
  const { i18n } = useTranslation();

  const languages = [
    { code: 'en-US', name: 'English (US)' },
    { code: 'en-GB', name: 'English (UK)' },
    // Future expansion ready
    // { code: 'es', name: 'Español' },
    // { code: 'fr', name: 'Français' },
    // { code: 'de', name: 'Deutsch' },
    // { code: 'ja', name: '日本語' },
  ];

  return (
    <Dropdown>
      <Dropdown.Toggle>
        {languages.find(l => l.code === i18n.language)?.name}
      </Dropdown.Toggle>
      <Dropdown.Menu>
        {languages.map(lang => (
          <Dropdown.Item
            key={lang.code}
            onClick={() => i18n.changeLanguage(lang.code)}
          >
            {lang.name}
          </Dropdown.Item>
        ))}
      </Dropdown.Menu>
    </Dropdown>
  );
}
```

## Theme System

### Theme Context with System Preference

```typescript
import { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'light' | 'dark' | 'auto';

interface ThemeContextType {
  theme: Theme;
  effectiveTheme: 'light' | 'dark';
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>(() => {
    return (localStorage.getItem('ollyscale-theme') as Theme) || 'auto';
  });

  const [effectiveTheme, setEffectiveTheme] = useState<'light' | 'dark'>('light');

  useEffect(() => {
    if (theme === 'auto') {
      const mediaQuery = window.matchMedia('(prefers-color-scheme: dark)');
      setEffectiveTheme(mediaQuery.matches ? 'dark' : 'light');

      const handler = (e: MediaQueryListEvent) => {
        setEffectiveTheme(e.matches ? 'dark' : 'light');
      };
      mediaQuery.addEventListener('change', handler);
      return () => mediaQuery.removeEventListener('change', handler);
    } else {
      setEffectiveTheme(theme);
    }
  }, [theme]);

  useEffect(() => {
    document.documentElement.setAttribute('data-bs-theme', effectiveTheme);
  }, [effectiveTheme]);

  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
    localStorage.setItem('ollyscale-theme', newTheme);
  };

  return (
    <ThemeContext.Provider value={{ theme, effectiveTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used within ThemeProvider');
  return context;
};
```

### Theme Toggle Component

```typescript
import { useTheme } from '../contexts/ThemeContext';
import { Sun, Moon, Circle } from 'react-bootstrap-icons';

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();

  return (
    <div className="btn-group" role="group">
      <button
        className={`btn btn-sm ${theme === 'light' ? 'btn-primary' : 'btn-outline-secondary'}`}
        onClick={() => setTheme('light')}
      >
        <Sun />
      </button>
      <button
        className={`btn btn-sm ${theme === 'dark' ? 'btn-primary' : 'btn-outline-secondary'}`}
        onClick={() => setTheme('dark')}
      >
        <Moon />
      </button>
      <button
        className={`btn btn-sm ${theme === 'auto' ? 'btn-primary' : 'btn-outline-secondary'}`}
        onClick={() => setTheme('auto')}
      >
        <Circle />
      </button>
    </div>
  );
}
```

## Testing Strategy

### Unit Tests with Vitest

```typescript
// __tests__/hooks/useAutoRefresh.test.ts
import { renderHook, act } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { useAutoRefresh } from '../../hooks/useAutoRefresh';

describe('useAutoRefresh', () => {
  it('should call refetch function on interval', () => {
    vi.useFakeTimers();
    const refetchFn = vi.fn();

    const { result } = renderHook(() => useAutoRefresh(refetchFn, 1000));

    expect(refetchFn).not.toHaveBeenCalled();

    act(() => {
      vi.advanceTimersByTime(1000);
    });

    expect(refetchFn).toHaveBeenCalledTimes(1);

    vi.useRealTimers();
  });

  it('should toggle auto-refresh', () => {
    const { result } = renderHook(() => useAutoRefresh(vi.fn()));

    expect(result.current.enabled).toBe(true);

    act(() => {
      result.current.toggle();
    });

    expect(result.current.enabled).toBe(false);
  });
});
```

### Component Tests

```typescript
// __tests__/components/TraceCard.test.tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { TraceCard } from '../../components/telemetry/TraceCard';

describe('TraceCard', () => {
  const mockTrace = {
    trace_id: 'abc123',
    service_name: 'test-service',
    name: 'GET /api/users',
    duration_seconds: 0.125,
    status_code: 200,
  };

  it('renders trace information', () => {
    render(<TraceCard trace={mockTrace} />);

    expect(screen.getByText('test-service')).toBeInTheDocument();
    expect(screen.getByText('GET /api/users')).toBeInTheDocument();
    expect(screen.getByText('125ms')).toBeInTheDocument();
  });

  it('displays status badge with correct color', () => {
    render(<TraceCard trace={mockTrace} />);

    const badge = screen.getByText('200');
    expect(badge).toHaveClass('badge-success');
  });
});
```

### Integration Tests with MSW

```typescript
// __tests__/integration/tracesFlow.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { setupServer } from 'msw/node';
import { http, HttpResponse } from 'msw';
import { describe, it, expect, beforeAll, afterAll } from 'vitest';
import { TracesPage } from '../../pages/TracesPage';

const server = setupServer(
  http.post('/api/traces/search', () => {
    return HttpResponse.json({
      traces: [
        { trace_id: 'abc123', service_name: 'test', name: 'GET /test' }
      ],
      pagination: { has_more: false }
    });
  })
);

beforeAll(() => server.listen());
afterAll(() => server.close());

describe('Traces Flow', () => {
  it('loads and displays traces', async () => {
    render(<TracesPage />);

    await waitFor(() => {
      expect(screen.getByText('test')).toBeInTheDocument();
    });
  });
});
```

### E2E Tests with Playwright

```typescript
// e2e/traces.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Traces Page', () => {
  test('should navigate to traces and view detail', async ({ page }) => {
    await page.goto('/');

    // Click traces tab
    await page.click('text=Traces');

    // Wait for traces to load
    await page.waitForSelector('.trace-card');

    // Click first trace
    await page.click('.trace-card:first-child');

    // Verify trace detail view
    await expect(page.locator('.trace-waterfall')).toBeVisible();
  });

  test('should apply query builder filter', async ({ page }) => {
    await page.goto('/traces');

    // Open query builder
    await page.click('text=Add Filter');

    // Select field
    await page.selectOption('[name="field"]', 'service.name');

    // Select operator
    await page.selectOption('[name="operator"]', 'eq');

    // Enter value
    await page.fill('[name="value"]', 'demo-frontend');

    // Apply filter
    await page.click('text=Apply Filter');

    // Verify filtered results
    await expect(page.locator('.trace-card')).toContainText('demo-frontend');
  });
});
```

## Open Questions

1. **Deployment Strategy**: Run old and new UI side-by-side during transition?
2. **Feature Flags**: Gradual rollout or full switch?
3. **Browser Support**: Target modern browsers only (ES2020+)?
4. **Mobile Support**: Full responsive or desktop-focused?
5. **Translation Contributors**: How to manage community translations?
6. **Telemetry Privacy**: User consent for browser telemetry collection?
7. **Sampling Rate**: What percentage of browser spans to sample

- **Badges**: Status-specific colors

## Auto-Refresh Implementation

```typescript
// hooks/useAutoRefresh.ts
export function useAutoRefresh(refetchFn: () => void, interval = 5000) {
  const [enabled, setEnabled] = useState(() => {
    return localStorage.getItem('ollyscale-auto-refresh') !== 'false';
  });

  useEffect(() => {
    if (!enabled) return;

    const intervalId = setInterval(refetchFn, interval);
    return () => clearInterval(intervalId);
  }, [enabled, interval, refetchFn]);

  const toggle = () => {
    setEnabled(!enabled);
    localStorage.setItem('ollyscale-auto-refresh', String(!enabled));
  };

  return { enabled, toggle };
}
```

## Embedded Documentation Strategy

### Documentation Sources

1. **Existing Docs**: Convert `docs/*.md` to React components
2. **Inline Help**: Contextual tooltips and popovers
3. **OpenAPI**: Embed API reference from `/api/docs`

### Documentation Navigation

```
Sidebar → Docs Tab → [Search Bar]
  ├── Quick Start
  ├── Features
  │   ├── Traces
  │   ├── Logs
  │   ├── Metrics
  │   └── Service Map
  ├── Query Builder Guide
  ├── API Reference
  └── Troubleshooting
```

### Markdown Rendering

```typescript
import ReactMarkdown from 'react-markdown';
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter';

<ReactMarkdown
  components={{
    code: ({ inline, className, children }) => {
      const match = /language-(\w+)/.exec(className || '');
      return !inline && match ? (
        <SyntaxHighlighter language={match[1]}>
          {String(children).replace(/\n$/, '')}
        </SyntaxHighlighter>
      ) : (
        <code className={className}>{children}</code>
      );
    }
  }}
>
  {docContent}
</ReactMarkdown>
```

## Migration from Current UI

### Feature Mapping

| Current UI Feature | New React Implementation |
|--------------------|--------------------------|
| Sidebar navigation | `Sidebar.tsx` with React Router |
| Auto-refresh toggle | `RefreshContext` + `useAutoRefresh` hook |
| Theme toggle | `ThemeContext` with Bootstrap themes |
| Namespace filter | `NamespaceContext` with multi-select dropdown |
| Text search | Query builder with "contains" operator |
| Status filters (2xx, 4xx, 5xx) | Query builder presets |
| Trace waterfall | `TraceWaterfall.tsx` with Recharts |
| Service map | React Cytoscape |
| Metrics charts | Recharts (replaces Chart.js) |
| JSON export | Maintained with `CopyButton`, `DownloadButton` |
| Log correlation | Maintained with context links |
| AI Agents view | New page with GenAI span rendering |
| Collector config | New page with Monaco editor |

## Success Criteria

### Branding & Visual Identity

- ✅ ollyScale logo and favicon preserved from current UI
- ✅ Logo displayed in sidebar header
- ✅ Logo used in loading spinner (animated rotation)
- ✅ Logo used in empty states (dimmed opacity)
- ✅ Consistent visual identity with current UI

### Functional Parity

- ✅ All current features work in new UI
- ✅ Query builder replaces text search with advanced filtering
- ✅ Auto-refresh works identically with pause detection
- ✅ Theme switching (light/dark/auto) persists
- ✅ All API endpoints consumed correctly
- ✅ Namespace filtering works across all views
- ✅ Export/download functionality maintained

### Performance

- ✅ Initial load < 2 seconds (on 4G)
- ✅ Time to Interactive (TTI) < 3 seconds
- ✅ First Contentful Paint (FCP) < 1.5 seconds
- ✅ Largest Contentful Paint (LCP) < 2.5 seconds
- ✅ Page transitions < 300ms
- ✅ Auto-refresh doesn't cause UI jank
- ✅ Large datasets handled with virtualization
- ✅ Bundle size < 500 KB gzipped

### Code Quality

- ✅ TypeScript strict mode passes
- ✅ ESLint with no warnings
- ✅ 80%+ test coverage (unit + component)
- ✅ E2E tests for critical paths
- ✅ Accessible (WCAG AA compliance)
- ✅ No console errors in production

### Internationalization

- ✅ 2 initial locales supported (en-US, en-GB)
- ✅ All UI strings translated with regional differences
- ✅ Date/time formatting per locale (US vs UK formats)
- ✅ Language switching works without reload
- ✅ Localized documentation available for both locales
- ✅ Framework ready for future language expansion

### Observability

- ✅ Browser telemetry capturing key metrics
- ✅ User interaction tracking working
- ✅ API call tracing with trace propagation
- ✅ Error tracking and reporting
- ✅ Web Vitals monitored

### Documentation

- ✅ Embedded docs cover all features
- ✅ Context-sensitive help works
- ✅ Search returns relevant results
- ✅ Documentation available in all languages
- ✅ API reference embedded and searchable

### Migration

- ✅ Beta period completed successfully
- ✅ User feedback addressed
- ✅ Smooth rollout with no downtime
- ✅ Old UI deprecated gracefully
- ✅ Migration guide published

## Timeline

| Phase | Duration | Deliverable |
|-------|----------|-------------|
| Phase 1-2 | 2 weeks | Infrastructure + API client |
| Phase 3 | 1 week | Query builder |
| Phase 4-5 | 2 weeks | Core pages (Traces, Logs, Metrics) |
| Phase 6-7 | 2 weeks | Services & advanced features |
| Phase 8 | 1.5 weeks | Embedded documentation |
| Phase 9 | 1 week | Auto-refresh & controls |
| Phase 10 | 1 week | Browser telemetry + i18n + themes |
| Phase 11 | 1 week | Infrastructure (OTel CR, HTTPRoute) & deployment |
| **Total** | **12 weeks** | Production-ready React UI |

## Additional Features to Consider (Future Enhancements)

### Phase 12+ (Post-Launch Enhancements)

#### Component Documentation (Storybook)

- [ ] Add Storybook for component library
- [ ] Document all reusable components
- [ ] Interactive component playground
- [ ] Accessibility testing in Storybook
- [ ] Visual regression testing with Chromatic

#### Advanced Features

- [ ] **PWA Support**: Service worker, offline mode, installable
- [ ] **Real-time Updates**: WebSockets or SSE for live data
- [ ] **Query Preset Sharing**: Export/import/share query builder filters
- [ ] **Keyboard Shortcuts**: Document and implement shortcuts (Ctrl+K for search)
- [ ] **Onboarding Tour**: First-time user tutorial
- [ ] **Collaborative Features**: Share links with filters, annotations
- [ ] **Custom Dashboards**: User-defined dashboard layouts
- [ ] **Alert Configuration UI**: UI for creating alerts (currently admin API only)
- [ ] **Data Export**: CSV, Excel, Parquet for bulk exports
- [ ] **Saved Views**: Bookmark specific filter/view combinations

#### Developer Experience

- [ ] API client SDK generation from OpenAPI
- [ ] GraphQL API consideration (for complex queries)
- [ ] WebSocket API for real-time streaming
- [ ] Mock API server for local development without backend
- [ ] Chrome DevTools extension for debugging

#### Analytics & Monitoring

- [ ] Usage analytics dashboard (admin only)
- [ ] Feature adoption tracking
- [ ] Error reporting dashboard (aggregate UI errors)
- [ ] User feedback mechanism (in-app surveys)
- [ ] A/B testing framework for new features

#### Enterprise Features

- [ ] SSO/SAML integration
- [ ] Role-based access control (RBAC)
- [ ] Multi-tenancy support
- [ ] Audit logging
- [ ] Data retention policies UI
- [ ] Cost attribution by namespace/service

## Browser Compatibility Matrix

**Target**: Modern browsers with ES2020+ support only

| Browser | Minimum Version | Support Level |
|---------|----------------|---------------|
| Chrome | 90+ | ✅ Primary (Desktop + Mobile) |
| Firefox | 88+ | ✅ Primary (Desktop + Mobile) |
| Safari | 14+ | ✅ Primary (Desktop + Mobile) |
| Edge | 90+ | ✅ Primary (Desktop + Mobile) |
| Samsung Internet | 14+ | ✅ Supported (Mobile) |

**Explicitly Not Supported**:

- IE11 (end of life)
- Opera Mini (no ES6 support)
- UC Browser (outdated engine)
- Legacy Android Browser
- Older Safari versions (<14)

**Mobile-First Responsive Design**:

- Touch-optimized interactions
- Mobile-friendly layouts (320px - 2560px)
- Breakpoints: xs (< 576px), sm (≥ 576px), md (≥ 768px), lg (≥ 992px), xl (≥ 1200px), xxl (≥ 1400px)
- Tested on iOS Safari and Chrome Mobile primarily

## Next Steps

1. **Review & Approve Plan**: Gather feedback on architecture and approach
2. **Phase 1 Kickoff**: Create `apps/react-ui/` and setup infrastructure
3. **Parallel Development**: Can work on API types while building UI
4. **Incremental Testing**: Test each phase before moving to next
5. **Documentation**: Update docs as features are completed

## Decisions Made

### Deployment & Rollout

- ✅ **Deployment**: Parallel if easy (new at `/`, old at `/legacy`), otherwise full replacement
- ✅ **Rollout**: Full switch, no gradual/feature-flag approach
- ✅ **Beta**: 1 week internal testing, then full launch
- ✅ **Legacy Access**: 2 weeks at `/legacy` post-launch, then remove

### Browser & Platform Support

- ✅ **Browsers**: Modern only (ES2020+), no legacy support
- ✅ **Mobile**: Full responsive support, mobile-first design
- ✅ **Target**: Chrome/Firefox/Safari/Edge 90+

### Internationalization

- ✅ **Launch Languages**: en-US (default), en-GB
- ✅ **Future Expansion**: es, fr, de, ja (framework prepared)
- ✅ **Date Formats**: US (MM/DD/YYYY) vs GB (DD/MM/YYYY)

## Open Questions (Remaining)

1. **Browser Telemetry Consent**: Show consent banner? GDPR compliance?
2. **Sampling Strategy**: 100% errors, 10% success - adjust based on volume?
3. **Translation Management**: Crowdin/Lokalise for future community translations?
4. **PWA Features**: Is offline mode valuable for observability tool?
5. **Real-time Updates**: WebSockets overhead worth it vs polling?
6. **Documentation Versioning**: Version docs with releases or keep single latest?
7. **Nginx Routing**: Serve both UIs from single container or separate deployments?

---

## Implementation Progress

### Completed Work (2026-01-30)

#### Phase 9: Auto-Refresh & Controls - COMPLETED ✅

**Implementation**: Sliding time window with live monitoring mode
**Branch**: `new-ui`
**Version**: `0.0.1769795574`

##### ✅ Sliding Time Window System

**Problem Solved**: Logs/traces not appearing despite auto-refresh being enabled - time range was fixed to page load time.

**Solution**: Implemented dynamic time window that slides forward on each auto-refresh when in "LIVE" mode.

**Implementation Details**:

1. **QueryContext Enhancement** ([apps/web-ui/src/contexts/QueryContext.tsx](../apps/web-ui/src/contexts/QueryContext.tsx)):

   ```typescript
   export interface QueryState {
     liveMode: boolean;           // Enable/disable sliding window
     relativeMinutes: number | null; // e.g., 30 for "last 30 minutes"
     timeRange: TimeRange;
   }

   const refreshTimeWindow = () => {
     // When in live mode, recalculate time range based on relative window
     if (prev.liveMode && prev.relativeMinutes) {
       const end = new Date();
       const start = new Date(end.getTime() - prev.relativeMinutes * 60 * 1000);
       return {
         ...prev,
         timeRange: {
           start_time: start.toISOString(),
           end_time: end.toISOString()
         }
       };
     }
   };
   ```

2. **LIVE/PAUSED Toggle UI** ([apps/web-ui/src/components/query/EnhancedQueryBuilder.tsx](../apps/web-ui/src/components/query/EnhancedQueryBuilder.tsx)):
   - Green "LIVE" button with broadcast icon when active
   - Gray "PAUSED" button with pause-circle icon when disabled
   - Automatically disables live mode when user manually adjusts time range
   - Time range preset buttons (5/15/30/60 minutes) enable live mode and highlight when active

3. **Page Integration**:
   - Updated all pages ([LogsPage.tsx](../apps/web-ui/src/pages/LogsPage.tsx), [TracesPage.tsx](../apps/web-ui/src/pages/TracesPage.tsx), [SpansPage.tsx](../apps/web-ui/src/pages/SpansPage.tsx), [MetricsPage.tsx](../apps/web-ui/src/pages/MetricsPage.tsx))
   - Auto-refresh now calls `refreshTimeWindow()` before `refetch()`
   - Ensures queries always use current time window in live mode

##### ✅ Timezone Display Enhancement

**Problem Solved**: Timestamps without timezone were ambiguous (UTC vs local time unclear).

**Solution**: Modified `formatTimestamp()` to append timezone abbreviation.

**Implementation**: [apps/web-ui/src/utils/formatting.ts](../apps/web-ui/src/utils/formatting.ts)

```typescript
export function formatTimestamp(isoString: string): string {
  const date = parseISO(isoString);
  const formatStr = 'MMM dd, yyyy HH:mm:ss.SSS';
  return format(date, formatStr) + ' ' + format(date, 'zzz');
  // Example output: "Jan 30, 2026 17:33:47.510 UTC"
}
```

**Impact**: All timestamps throughout UI now clearly show timezone context.

##### ✅ Static Assets Fix

**Problem**: 404 errors for `/logo.svg` and `/favicon.svg` when accessing deployed UI.

**Root Cause**: Dockerfile missing `COPY public/ ./public/` step before Vite build.

**Solution**: Added public directory copy to [Dockerfile](../apps/web-ui/Dockerfile) at line 21.

**Result**: All static assets now serve correctly (HTTP 200).

##### ✅ Deployment & Validation

- Built and deployed version `0.0.1769795574` to KIND cluster
- All pods running successfully (api, otlp-receiver, webui, legacyui, db)
- ArgoCD application healthy
- Committed 19 commits to `new-ui` branch
- Pushed to GitHub: <https://github.com/ryanfaircloth/ollyscale/tree/new-ui>

##### Behavior Validation

**Live Mode (Default)**:

1. User opens Logs page → LIVE mode enabled by default
2. Clicks "30 minutes" button → Time range set to "last 30 minutes from now"
3. Auto-refresh triggers (every 5 seconds) → Time window slides forward
4. New logs continuously appear as they're ingested
5. LIVE button shows green with broadcast icon

**Paused Mode**:

1. User manually adjusts start/end time → LIVE mode auto-disables
2. LIVE button turns gray "PAUSED" with pause-circle icon
3. Auto-refresh triggers → Time range stays fixed
4. User can click LIVE button → Resume sliding window

**Persistence**:

- Live mode state persisted to localStorage
- Survives page reloads
- Independent per browser/device

---

## Current Status Summary (2026-01-31)

### ✅ What's Working

- Core UI framework (React 19, Vite, TypeScript, Bootstrap)
- All 9 pages exist (Dashboard, Traces, Spans, Logs, Metrics, Services, Service Map, AI Agents, Collector Config)
- Service Map fully functional with 5 services
- Query filtering (custom implementation)
- Auto-refresh with sliding time window
- Charts and visualizations
- Kubernetes deployment active

### ⚠️ Technical Debt

- **react-querybuilder**: Installed but NOT used (600KB wasted)
  - **Decision Required**: Refactor to use library OR remove dependency

### ❌ Critical Missing Infrastructure

1. **Testing** (0% complete):
   - No testing libraries installed
   - 0 test files exist
   - No test configuration

2. **Internationalization** (0% complete):
   - No i18n libraries installed
   - All strings hardcoded in English
   - No locale files

3. ~~**Browser Telemetry**~~ ✅ (100% complete):
   - ✅ OpenTelemetry browser SDK with auto-instrumentation
   - ✅ Error handlers (global, promise rejection, React boundary)
   - ✅ Custom span tracking for user actions
   - ✅ Tail sampling configuration (keep all non-receiver spans)
   - ⚠️ GDPR consent management not implemented (deferred)

### 🔄 Partially Complete

- AI Agents page (structure exists, functionality missing)
- Collector Config page (structure exists, functionality missing)
- PWA setup (vite-plugin-pwa installed, not configured)

---

## Next Steps (Priority Order)

### 1. Resolve Query Builder Technical Debt (⏱️ 1-2 days)

**Decision Required**: Choose one:

- **Option A**: Refactor to use react-querybuilder properly (recommended for maintainability)
- **Option B**: Remove react-querybuilder dependency (saves 600KB, keeps custom code)

### 2. Install Testing Infrastructure (⏱️ 1-2 days)

```bash
cd apps/web-ui
npm install -D vitest @vitest/ui
npm install -D @testing-library/react @testing-library/jest-dom @testing-library/user-event
npm install -D msw happy-dom @playwright/test
```

- Configure vitest.config.ts
- Write first test to validate setup
- Add to CI/CD

### 3. ~~Install Internationalization~~ ✅ COMPLETED (2026-02-01)

```bash
cd apps/web-ui
npm install react-i18next i18next i18next-browser-languagedetector
```

- ✅ Created i18n/config.ts configuration with language detection
- ✅ Extracted hardcoded strings to translation files (en-US: 287 keys, en-GB with UK variants)
- ✅ Added LanguageSelector component with flag dropdowns (🇺🇸/🇬🇧)
- ✅ Updated all pages, sidebar, and common components with useTranslation() hook
- ✅ Language persistence via localStorage
- ✅ Deployed and tested in Kubernetes

**Commit**: 1a166f2 - feat(web-ui): implement internationalization (i18n) support

### 4. ~~Browser Telemetry Setup~~ ✅ COMPLETE (2026-02-02)

**All browser telemetry features implemented and tested:**

**Completed Tasks**:

- ✅ Global error handler (`window.onerror`) capturing unhandled exceptions
- ✅ Promise rejection handler (`window.onunhandledrejection`) for async errors
- ✅ ErrorBoundary component catching React component errors
- ✅ Custom events for user actions (custom_event, slow_operation, manual_error_test)
- ✅ Tail sampling strategy: Keep ALL spans except 95% of successful receiver spans
- ✅ End-to-end verification: All 6 test buttons working

**Files Modified**:

- ✅ `src/telemetry/config.ts` - Global error handlers with span creation
- ✅ `src/components/ErrorBoundary.tsx` - React error boundary with telemetry
- ✅ `src/App.tsx` - Wrapped with ErrorBoundary
- ✅ `src/hooks/useTracing.ts` - Custom span creation methods
- ✅ `charts/ollyscale/values.yaml` - Simplified tail_sampling configuration

**Verified Working Spans** (from database):

1. `error.unhandled` - Synchronous errors
2. `error.unhandled_rejection` - Promise rejections
3. `error.react_boundary` - React component errors
4. `user.action.manual_error_test` - Manual error recording
5. `user.action.slow_operation` - Performance tracking
6. `user.action.custom_event` - Custom user events

**Root Cause Fixed**: Gateway collector tail_sampling was dropping non-error web-ui spans. Simplified to keep all spans by default.

**Commit**: 8dab0b4 - fix(collector): simplify tail_sampling to keep all non-receiver spans

### 5. Phase 10.4: Quick Wins + Critical Features (⏱️ 2 days) - PRIORITY 1 (IN PROGRESS)

**Rationale**: Implement high-impact, low-effort features before moving to testing phase. Focus on navigation/UX improvements and critical Service Catalog RED metrics.

**Tasks**:

#### 5.1. Service Catalog Navigation Buttons (⏱️ 3 hours) - ✅ COMPLETED (2026-02-02)

- [x] Add "View Spans" button → Navigate to /spans with service_name filter
- [x] Add "View Logs" button → Navigate to /logs with service_name filter
- [x] Add "View Metrics" button → Navigate to /metrics with service_name filter
- [x] Update QueryContext to accept initial filters from navigation state
- [x] Test navigation flow from Service Catalog

**Files modified**:

- `apps/web-ui/src/pages/ServiceCatalogPage.tsx` - Added navigation buttons to service rows
- `apps/web-ui/src/pages/LogsPage.tsx` - Added location.state handling for initial filters
- `apps/web-ui/src/pages/SpansPage.tsx` - Added location.state handling for initial filters
- `apps/web-ui/src/pages/MetricsPage.tsx` - Added location.state handling for initial filters

**Commit**: f1a8a9a - feat(web-ui): add service catalog navigation buttons

#### 5.2. View Metrics from Traces/Spans (⏱️ 1 hour) - ✅ COMPLETED (2026-02-02)

- [x] Add "View Metrics" button in TraceModal → Navigate with service filter
- [x] Add "View Metrics" button in SpanDetail → Navigate with service filter
- [x] Test navigation from trace/span details

**Files modified**:

- `apps/web-ui/src/components/trace/TraceModal.tsx` - Added View Metrics button
- `apps/web-ui/src/components/trace/SpanDetail.tsx` - Added View Metrics button

**Commit**: f36cd34 - feat(web-ui): add view metrics buttons to trace and span modals

#### 5.3. Separate Spans Tab in Sidebar (⏱️ 2 hours) - ✅ ALREADY COMPLETE

- [x] Add "Spans" tab to Sidebar.tsx (between Traces and Logs)
- [x] Ensure SpansPage is accessible at /spans route
- [x] Test navigation and active state highlighting
- [x] Update translations (en-US, en-GB) with "Spans" label

**Status**: Already implemented in earlier phases. All requirements satisfied:

- Sidebar includes Spans nav item with icon 'layers' and labelKey 'nav.spans'
- Route configured in App.tsx at `/spans` with SpansPage component
- Translations exist: `nav.spans: "Spans"` in both en-US and en-GB
- Active state highlighting works via React Router NavLink

**No changes needed**.

#### 5.4. Service Catalog RED Metrics (⏱️ 1-2 days) - ✅ COMPLETED (2026-02-02)

- [x] Fetch RED metrics from backend API (already implemented)
- [x] Display Rate (requests/min) in table column with total count
- [x] Display Error rate (%) in table column with color coding
- [x] Display Duration (p50/p95/p99) in table columns
- [x] Format metrics with proper units and precision
- [x] Backend already provides loading states
- [x] Tested with PostgreSQL storage backend

**Files modified**:

- `apps/web-ui/src/pages/ServiceCatalogPage.tsx` - Enhanced RED metrics display

**Implementation details**:

- Rate calculation: `requestCount / timeRangeDurationMinutes` with format "45.2 (1234)" showing req/min and total
- Error rate: Color-coded badges (green: 0%, yellow: <1%, red: ≥1%)
- Latency: P50/P95/P99 displayed with formatDuration(), P95 color-coded by threshold (<100ms green, <500ms yellow, else red)
- P99 shown in red text to indicate worst-case latency
- Backend API returns complete ServiceMetrics: request_count, error_count, error_rate, p50/p95/p99_latency_ms
- Time range: Last 30 minutes (hardcoded in page state)

**Commit**: 80b16b0 - feat(web-ui): enhance service catalog with complete RED metrics

#### 5.5. Service Catalog Column Sorting (⏱️ 3 hours) - ✅ COMPLETED (2026-02-02)

- [x] Add sort state management (column, direction) with useLocalStorage
- [x] Add sort icons to table headers (bi-arrow-up/down icons)
- [x] Implement client-side sorting for all columns (name, namespace, rate, error_rate, p50, p95, p99)
- [x] Persist sort preference to localStorage (service-catalog-sort key)
- [x] Test sorting with all columns

**Files modified**:

- `apps/web-ui/src/pages/ServiceCatalogPage.tsx` - Added complete sorting logic

**Implementation details**:

- **Sort state**: `useLocalStorage<{column: string, direction: 'asc'|'desc'}>` with key 'service-catalog-sort'
- **Default sort**: service name ascending
- **Sortable columns**: name, namespace, rate (req/min), error_rate (%), p50/p95/p99 latencies (ms)
- **Visual indicators**: Bootstrap Icons (bi-arrow-up, bi-arrow-down) shown next to active column
- **Click behavior**: First click sorts ascending, second click sorts descending, clicking another column resets to ascending
- **String sorting**: Case-insensitive with localeCompare for name/namespace
- **Numeric sorting**: Type-safe comparison with fallback to 0 for undefined values
- **Performance**: useMemo for sorted array, only recomputes when data or sort config changes

**Commit**: ada96e0 - feat(web-ui): add column sorting to service catalog

---

## Phase 10.4 Summary - ✅ COMPLETED (2026-02-02)

**All 5 tasks completed successfully:**

1. ✅ Service Catalog Navigation Buttons (f1a8a9a)
2. ✅ View Metrics from Traces/Spans (f36cd34)
3. ✅ Separate Spans Tab (already existed)
4. ✅ Service Catalog RED Metrics (80b16b0)
5. ✅ Column Sorting (ada96e0)

**Success Criteria Met:**

- ✅ All navigation buttons work correctly with filters applied
- ✅ Spans tab visible in sidebar with proper routing
- ✅ Service Catalog displays Rate, Error, Duration metrics
- ✅ Table sorting works for all numeric and string columns
- ✅ No TypeScript errors
- ✅ All pre-commit hooks pass

**Deployment Ready**: All features implemented, tested, and committed. Ready to proceed to Phase 10.1 (Write Comprehensive Tests).

**Deployment Plan**:

1. Implement features incrementally (commit after each task)
2. Build and deploy to Kubernetes after all tasks complete
3. Manual testing of navigation flows
4. Verify RED metrics accuracy against backend data
5. Commit with conventional commit message

**After Completion**: Proceed to Phase 10.1 (Write Comprehensive Tests)

### 6. Write Comprehensive Tests (⏱️ 3-4 days) - PRIORITY 2

Testing infrastructure is installed, but only 1 test file exists.

```bash
cd apps/web-ui
npm install -D msw@latest  # Install MSW for API mocking
```

**Priority tests to write**:

- [ ] Hook tests: useAutoRefresh, useLocalStorage, useTracing, useQuery
- [ ] Utility tests: date formatting, validators, helpers
- [ ] Component tests: QueryBuilder, TraceWaterfall, ServiceGraph
- [ ] Page tests: basic rendering, loading states, error states
- [ ] API client tests with MSW mocks
- [ ] Integration tests: complete user flows

### 6. Complete AI Agents Page (⏱️ 2-3 days) - PRIORITY 3

- GenAI span visualization
- Token tracking display (input/output tokens)
- Prompt/response viewer
- Model filtering

### 6. Complete Collector Config Page (⏱️ 2-3 days)

- OpAMP status display
- Configuration viewer/editor
- Apply changes functionality

### 7. Write Tests (⏱️ ongoing)

- Unit tests for hooks and utils
- Component tests for pages
- Integration tests with MSW
- E2E tests with Playwright (optional)

### 8. Performance & Accessibility (⏱️ 1 week)

- React.memo for expensive components
- Bundle size optimization
- Keyboard navigation
- ARIA labels
- Color contrast audit

---

**Total Estimated Work**: 1-2 weeks for critical infrastructure + ongoing testing

**Last Updated**: 2026-02-02 (Phase 10.4 planning complete)
**Current Status**: Phases 1-6, 9, 10.2, 10.3 COMPLETE - Core UI with i18n and full browser telemetry deployed
**Next Phase**: Phase 10.4 (Quick Wins + RED Metrics) - IN PROGRESS
**After 10.4**: Phase 10.1 (Write Comprehensive Tests)
**Source of Truth**: This plan is now the single source of truth (react-ui-decisions.md and react-ui-implementation-status.md removed)

- Survives page reloads
- Independent per browser/device

##### Files Modified

- ✅ [apps/web-ui/src/contexts/QueryContext.tsx](../apps/web-ui/src/contexts/QueryContext.tsx) - Added liveMode, relativeMinutes, refreshTimeWindow()
- ✅ [apps/web-ui/src/utils/formatting.ts](../apps/web-ui/src/utils/formatting.ts) - Added timezone to formatTimestamp()
- ✅ [apps/web-ui/src/components/query/EnhancedQueryBuilder.tsx](../apps/web-ui/src/components/query/EnhancedQueryBuilder.tsx) - Added LIVE/PAUSED toggle
- ✅ [apps/web-ui/src/pages/LogsPage.tsx](../apps/web-ui/src/pages/LogsPage.tsx) - Integrated refreshTimeWindow()
- ✅ [apps/web-ui/src/pages/TracesPage.tsx](../apps/web-ui/src/pages/TracesPage.tsx) - Integrated refreshTimeWindow()
- ✅ [apps/web-ui/src/pages/SpansPage.tsx](../apps/web-ui/src/pages/SpansPage.tsx) - Integrated refreshTimeWindow()
- ✅ [apps/web-ui/src/pages/MetricsPage.tsx](../apps/web-ui/src/pages/MetricsPage.tsx) - Integrated refreshTimeWindow()
- ✅ [apps/web-ui/Dockerfile](../apps/web-ui/Dockerfile) - Fixed static assets copy

##### Test Results

✅ **TypeScript Compilation**: Clean build with no errors
✅ **Pre-commit Hooks**: All checks passed (ESLint, Prettier, Helm lint)
✅ **Static Assets**: logo.svg, favicon.svg serving correctly (HTTP 200)
✅ **API Integration**: Logs API returning data correctly with time ranges
✅ **Deployment**: All pods running, ArgoCD healthy

##### Technical Debt & Future Improvements

- Consider adding visual indicator when time window slides (subtle animation)
- Add "time window size" badge showing current relative window (e.g., "Last 30 min")
- Consider keyboard shortcut to toggle live mode (e.g., 'L' key)
- Add "sync to now" button for quickly updating paused time ranges
- Consider per-page live mode preferences (e.g., always live for Logs, paused for Metrics)

---

**Plan Status**: ✅ 75% Complete - Phases 1-6, 9, 10.2, 10.3 DONE | Next: Phase 10.4 (Quick Wins + RED Metrics)
**Last Updated**: 2026-02-02 (Phase 10.4 planning complete)
**Owner**: Ryan Faircloth
**Deployed**: ollyscale-webui active on Kubernetes at ollyscale.ollyscale.test
