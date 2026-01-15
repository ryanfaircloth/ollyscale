# Changelog

All notable changes to the TinyOlly UI component will be documented in this file.

## 1.0.0 (2026-01-15)


### Features

* **ui:** refactor to separate static UI from FastAPI backend ([843b7a4](https://github.com/ryanfaircloth/tinyolly/commit/843b7a48c944af54e8de1cb2a6bff70d0837d83c))


### Bug Fixes

* **ui:** restore missing HTML structure in index.html ([e6a341f](https://github.com/ryanfaircloth/tinyolly/commit/e6a341f49193bc098b4d90f241b142363d45bba8))
* **ui:** update Vite to 6.4.1 to resolve esbuild security vulnerability ([5af2222](https://github.com/ryanfaircloth/tinyolly/commit/5af2222436bac03e41ab8b8a181cc259b1f88b6a))

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
