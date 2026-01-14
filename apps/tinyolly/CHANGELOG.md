# Changelog

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
