import { StrictMode } from 'react';
import { createRoot } from 'react-dom/client';
import './styles/main.scss';
import 'bootstrap-icons/font/bootstrap-icons.css';
import './i18n/config'; // Initialize i18next
import App from './App.tsx';
import { initializeTelemetry } from './telemetry/config';

// Initialize OpenTelemetry if user has already consented
// (consent banner will initialize if not yet consented)
initializeTelemetry();

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>
);
