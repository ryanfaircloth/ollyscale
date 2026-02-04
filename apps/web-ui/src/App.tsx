import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { RefreshProvider } from '@/contexts/RefreshContext';
import { QueryProvider } from '@/contexts/QueryContext';
import { ConsentBanner } from '@/components/ConsentBanner';
import { ErrorBoundary } from '@/components/common/ErrorBoundary';
import AppLayout from '@/components/layout/AppLayout';
import TracesPage from '@/pages/TracesPage';
import LogsPage from '@/pages/LogsPage';
import MetricsPage from '@/pages/MetricsPage';
import SpansPage from '@/pages/SpansPage';
import ServiceCatalogPage from '@/pages/ServiceCatalogPage';
import ServiceMapPage from '@/pages/ServiceMapPage';
import AIAgentsPage from '@/pages/AIAgentsPage';
import OtelConfigPage from '@/pages/OtelConfigPage';
import DashboardPage from '@/pages/DashboardPage';
import { TelemetryTestPage } from '@/pages/TelemetryTestPage';

// Create QueryClient instance
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      refetchOnWindowFocus: false,
      retry: 1,
      staleTime: 5000,
    },
  },
});

function App() {
  return (
    <ErrorBoundary>
      <QueryClientProvider client={queryClient}>
        <ThemeProvider>
          <RefreshProvider>
            <QueryProvider>
              <BrowserRouter>
                <ConsentBanner />
                <Routes>
                  <Route path="/" element={<AppLayout />}>
                    <Route index element={<Navigate to="/dashboard" replace />} />
                    <Route path="dashboard" element={<DashboardPage />} />
                    <Route path="logs" element={<LogsPage />} />
                    <Route path="metrics" element={<MetricsPage />} />
                    <Route path="traces" element={<TracesPage />} />
                    <Route path="spans" element={<SpansPage />} />
                    <Route path="catalog" element={<ServiceCatalogPage />} />
                    <Route path="map" element={<ServiceMapPage />} />
                    <Route path="ai-agents" element={<AIAgentsPage />} />
                    <Route path="collector" element={<OtelConfigPage />} />
                    {/* Hidden test page - not in navigation */}
                    <Route path="telemetry-test" element={<TelemetryTestPage />} />
                    <Route path="*" element={<div><h2>Page Not Found</h2></div>} />
                  </Route>
              </Routes>
            </BrowserRouter>
          </QueryProvider>
        </RefreshProvider>
      </ThemeProvider>
    </QueryClientProvider>
    </ErrorBoundary>  );
}

export default App;
