# ollyScale UI

Modern frontend for ollyScale observability platform built with Vite and TypeScript.

This component provides the user interface for viewing traces, logs, metrics, and service maps.

## Architecture

- **Build System**: Vite for fast builds and HMR
- **Runtime**: nginx on Alpine Linux (port 8000)
- **Dependencies**: Bundled (Cytoscape.js, Chart.js) - no CDN
- **Backend**: Proxies API requests to FastAPI frontend service

## Development

```bash
# Install dependencies
npm install

# Run dev server with HMR (proxies to backend at localhost:5002)
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Build Process

1. **Build stage**: Node.js compiles TypeScript, bundles JS/CSS with Vite
2. **Runtime stage**: nginx Alpine serves static files on port 8000, proxies API calls

## Project Structure

```text
src/
  index.html          # Main HTML template
  main.ts             # Entry point
  styles/             # CSS modules
  modules/            # JS modules (api, render, etc.)
  assets/             # Static assets (logo, favicon)
nginx/
  nginx.conf          # nginx configuration
  default.conf        # Site configuration
Dockerfile            # Multi-stage build
```
