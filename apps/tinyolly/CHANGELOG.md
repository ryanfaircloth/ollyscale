# Changelog

## [37.0.0](https://github.com/ryanfaircloth/tinyolly/compare/v36.0.0...v37.0.0) (2026-01-15)


### ⚠ BREAKING CHANGES

* Release process now uses conventional commits and release-please
* Major folder restructure from scattered layout to organized monorepo

### Features

* implement release-please for automated semantic versioning ([d5591e9](https://github.com/ryanfaircloth/tinyolly/commit/d5591e9c26d07d072cb589ccace52bdd705df13e))
* Migrate ai-agent demo to Helm with OTel operator auto-instrumentation ([9f93796](https://github.com/ryanfaircloth/tinyolly/commit/9f93796a5f9e926c3b5a89c588cef7fed95ab563))
* **ui:** refactor to separate static UI from FastAPI backend ([843b7a4](https://github.com/ryanfaircloth/tinyolly/commit/843b7a48c944af54e8de1cb2a6bff70d0837d83c))


### Bug Fixes

* **apps:** force rebuild of all containers after VERSION file removal ([d21b4f7](https://github.com/ryanfaircloth/tinyolly/commit/d21b4f7eb6eca71c36cd245e915688737fc47781))
* consolidate CI workflows and resolve all linting errors ([1ea8973](https://github.com/ryanfaircloth/tinyolly/commit/1ea8973de8c46c6eb8ff31b4aa91e3790f65a562))
* correct fixture name reference in tests ([2c540b7](https://github.com/ryanfaircloth/tinyolly/commit/2c540b70d58849e89f7747270cb3fde173c82958))
* remove ai-agent-demo from build script + add noqa for telemetry ([17f3b2b](https://github.com/ryanfaircloth/tinyolly/commit/17f3b2b43cba70ff68df818ed67f2df538892d09))
* remove VERSION files entirely ([b3856ae](https://github.com/ryanfaircloth/tinyolly/commit/b3856aebc2baa3758c0278a00d3f567acac8e388))
* use manifest as single source of truth for versions ([e9f9530](https://github.com/ryanfaircloth/tinyolly/commit/e9f95302a2e26a5409caedf79165a35d384cecf3))


### Code Refactoring

* **backend:** remove obsolete static and templates directories ([6c67eb7](https://github.com/ryanfaircloth/tinyolly/commit/6c67eb701bdc48ff37d7ca35b5369c1ee9ff2bb9))
* restructure repository to standard monorepo layout ([1d0afcf](https://github.com/ryanfaircloth/tinyolly/commit/1d0afcf4f6ee8ebe2c921c4e96a65d56f5d9436d))
* switch to local-only development builds ([d78ba92](https://github.com/ryanfaircloth/tinyolly/commit/d78ba920d14708572cdc4ee32c773c24eed2eefc))

## [36.0.0](https://github.com/ryanfaircloth/tinyolly/compare/v35.0.0...v36.0.0) (2026-01-14)


### ⚠ BREAKING CHANGES

* Release process now uses conventional commits and release-please
* Major folder restructure from scattered layout to organized monorepo

### Features

* implement release-please for automated semantic versioning ([d5591e9](https://github.com/ryanfaircloth/tinyolly/commit/d5591e9c26d07d072cb589ccace52bdd705df13e))
* Migrate ai-agent demo to Helm with OTel operator auto-instrumentation ([9f93796](https://github.com/ryanfaircloth/tinyolly/commit/9f93796a5f9e926c3b5a89c588cef7fed95ab563))


### Bug Fixes

* **apps:** force rebuild of all containers after VERSION file removal ([d21b4f7](https://github.com/ryanfaircloth/tinyolly/commit/d21b4f7eb6eca71c36cd245e915688737fc47781))
* consolidate CI workflows and resolve all linting errors ([1ea8973](https://github.com/ryanfaircloth/tinyolly/commit/1ea8973de8c46c6eb8ff31b4aa91e3790f65a562))
* correct fixture name reference in tests ([2c540b7](https://github.com/ryanfaircloth/tinyolly/commit/2c540b70d58849e89f7747270cb3fde173c82958))
* remove ai-agent-demo from build script + add noqa for telemetry ([17f3b2b](https://github.com/ryanfaircloth/tinyolly/commit/17f3b2b43cba70ff68df818ed67f2df538892d09))
* remove VERSION files entirely ([b3856ae](https://github.com/ryanfaircloth/tinyolly/commit/b3856aebc2baa3758c0278a00d3f567acac8e388))
* use manifest as single source of truth for versions ([e9f9530](https://github.com/ryanfaircloth/tinyolly/commit/e9f95302a2e26a5409caedf79165a35d384cecf3))


### Code Refactoring

* restructure repository to standard monorepo layout ([1d0afcf](https://github.com/ryanfaircloth/tinyolly/commit/1d0afcf4f6ee8ebe2c921c4e96a65d56f5d9436d))

## [35.0.0](https://github.com/ryanfaircloth/tinyolly/compare/v34.0.1...v35.0.0) (2026-01-14)


### ⚠ BREAKING CHANGES

* Release process now uses conventional commits and release-please
* Major folder restructure from scattered layout to organized monorepo

### Features

* implement release-please for automated semantic versioning ([d5591e9](https://github.com/ryanfaircloth/tinyolly/commit/d5591e9c26d07d072cb589ccace52bdd705df13e))
* Migrate ai-agent demo to Helm with OTel operator auto-instrumentation ([9f93796](https://github.com/ryanfaircloth/tinyolly/commit/9f93796a5f9e926c3b5a89c588cef7fed95ab563))


### Bug Fixes

* **apps:** force rebuild of all containers after VERSION file removal ([d21b4f7](https://github.com/ryanfaircloth/tinyolly/commit/d21b4f7eb6eca71c36cd245e915688737fc47781))
* consolidate CI workflows and resolve all linting errors ([1ea8973](https://github.com/ryanfaircloth/tinyolly/commit/1ea8973de8c46c6eb8ff31b4aa91e3790f65a562))
* correct fixture name reference in tests ([2c540b7](https://github.com/ryanfaircloth/tinyolly/commit/2c540b70d58849e89f7747270cb3fde173c82958))
* remove ai-agent-demo from build script + add noqa for telemetry ([17f3b2b](https://github.com/ryanfaircloth/tinyolly/commit/17f3b2b43cba70ff68df818ed67f2df538892d09))
* remove VERSION files entirely ([b3856ae](https://github.com/ryanfaircloth/tinyolly/commit/b3856aebc2baa3758c0278a00d3f567acac8e388))
* use manifest as single source of truth for versions ([e9f9530](https://github.com/ryanfaircloth/tinyolly/commit/e9f95302a2e26a5409caedf79165a35d384cecf3))


### Code Refactoring

* restructure repository to standard monorepo layout ([1d0afcf](https://github.com/ryanfaircloth/tinyolly/commit/1d0afcf4f6ee8ebe2c921c4e96a65d56f5d9436d))

## [34.0.0](https://github.com/ryanfaircloth/tinyolly/compare/v33.0.0...v34.0.0) (2026-01-14)


### ⚠ BREAKING CHANGES

* Release process now uses conventional commits and release-please
* Major folder restructure from scattered layout to organized monorepo

### Features

* implement release-please for automated semantic versioning ([d5591e9](https://github.com/ryanfaircloth/tinyolly/commit/d5591e9c26d07d072cb589ccace52bdd705df13e))
* Migrate ai-agent demo to Helm with OTel operator auto-instrumentation ([9f93796](https://github.com/ryanfaircloth/tinyolly/commit/9f93796a5f9e926c3b5a89c588cef7fed95ab563))


### Bug Fixes

* consolidate CI workflows and resolve all linting errors ([1ea8973](https://github.com/ryanfaircloth/tinyolly/commit/1ea8973de8c46c6eb8ff31b4aa91e3790f65a562))
* correct fixture name reference in tests ([2c540b7](https://github.com/ryanfaircloth/tinyolly/commit/2c540b70d58849e89f7747270cb3fde173c82958))
* remove ai-agent-demo from build script + add noqa for telemetry ([17f3b2b](https://github.com/ryanfaircloth/tinyolly/commit/17f3b2b43cba70ff68df818ed67f2df538892d09))


### Code Refactoring

* restructure repository to standard monorepo layout ([1d0afcf](https://github.com/ryanfaircloth/tinyolly/commit/1d0afcf4f6ee8ebe2c921c4e96a65d56f5d9436d))

## [33.0.0](https://github.com/ryanfaircloth/tinyolly/compare/v32.0.0...v33.0.0) (2026-01-14)


### ⚠ BREAKING CHANGES

* Release process now uses conventional commits and release-please
* Major folder restructure from scattered layout to organized monorepo

### Features

* implement release-please for automated semantic versioning ([d5591e9](https://github.com/ryanfaircloth/tinyolly/commit/d5591e9c26d07d072cb589ccace52bdd705df13e))
* Migrate ai-agent demo to Helm with OTel operator auto-instrumentation ([9f93796](https://github.com/ryanfaircloth/tinyolly/commit/9f93796a5f9e926c3b5a89c588cef7fed95ab563))


### Bug Fixes

* consolidate CI workflows and resolve all linting errors ([1ea8973](https://github.com/ryanfaircloth/tinyolly/commit/1ea8973de8c46c6eb8ff31b4aa91e3790f65a562))
* correct fixture name reference in tests ([2c540b7](https://github.com/ryanfaircloth/tinyolly/commit/2c540b70d58849e89f7747270cb3fde173c82958))
* remove ai-agent-demo from build script + add noqa for telemetry ([17f3b2b](https://github.com/ryanfaircloth/tinyolly/commit/17f3b2b43cba70ff68df818ed67f2df538892d09))


### Code Refactoring

* restructure repository to standard monorepo layout ([1d0afcf](https://github.com/ryanfaircloth/tinyolly/commit/1d0afcf4f6ee8ebe2c921c4e96a65d56f5d9436d))

## [32.0.0](https://github.com/ryanfaircloth/tinyolly/compare/v31.0.3...v32.0.0) (2026-01-14)


### ⚠ BREAKING CHANGES

* Release process now uses conventional commits and release-please
* Major folder restructure from scattered layout to organized monorepo

### Features

* implement release-please for automated semantic versioning ([d5591e9](https://github.com/ryanfaircloth/tinyolly/commit/d5591e9c26d07d072cb589ccace52bdd705df13e))
* Migrate ai-agent demo to Helm with OTel operator auto-instrumentation ([9f93796](https://github.com/ryanfaircloth/tinyolly/commit/9f93796a5f9e926c3b5a89c588cef7fed95ab563))


### Bug Fixes

* consolidate CI workflows and resolve all linting errors ([1ea8973](https://github.com/ryanfaircloth/tinyolly/commit/1ea8973de8c46c6eb8ff31b4aa91e3790f65a562))
* correct fixture name reference in tests ([2c540b7](https://github.com/ryanfaircloth/tinyolly/commit/2c540b70d58849e89f7747270cb3fde173c82958))
* remove ai-agent-demo from build script + add noqa for telemetry ([17f3b2b](https://github.com/ryanfaircloth/tinyolly/commit/17f3b2b43cba70ff68df818ed67f2df538892d09))


### Code Refactoring

* restructure repository to standard monorepo layout ([1d0afcf](https://github.com/ryanfaircloth/tinyolly/commit/1d0afcf4f6ee8ebe2c921c4e96a65d56f5d9436d))
