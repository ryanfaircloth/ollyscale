# Changelog

All notable changes to the TinyOlly UI component will be documented in this file.

## [2.0.0] - 2025-01-14

### Added

- Modern frontend build system with Vite
- TypeScript support with proper type checking
- npm package management with bundled dependencies
- Cytoscape.js bundled (no CDN)
- Chart.js bundled (no CDN)
- Alpine Linux + nginx container for static file serving on port 8000
- Multi-stage Docker build (Node.js build + nginx runtime)
- Proper caching headers and gzip compression
- API proxy configuration to FastAPI frontend service
- Development server with Hot Module Replacement (HMR)
- ESLint and Prettier for code quality
- Production-optimized bundle with minification

### Changed

- Migrated from Python-served static files to dedicated nginx container
- Removed CDN dependencies in favor of bundled npm packages
- Improved build process with proper asset hashing
- Better separation of concerns (UI container vs API container)
- Port changed to 8000 for nginx service

### Technical Details

- Base image: nginx:1.25-alpine
- Build tool: Vite 5.x
- Package manager: npm
- Runtime port: 8000
- Runtime: nginx with proxy_pass to FastAPI frontend service
