# Changelog

## [0.2.1](https://github.com/ryanfaircloth/tinyolly/compare/helm-tinyolly-v0.2.0...helm-tinyolly-v0.2.1) (2026-01-14)


### Features

* simplify local dev - make build creates tfvars ([78dfeb1](https://github.com/ryanfaircloth/tinyolly/commit/78dfeb1ac0f9a73ea7e0ceff8730c56c5e9af78b))


### Bug Fixes

* consolidate CI workflows and resolve all linting errors ([1ea8973](https://github.com/ryanfaircloth/tinyolly/commit/1ea8973de8c46c6eb8ff31b4aa91e3790f65a562))
* remove ai-agent-demo from build script + add noqa for telemetry ([17f3b2b](https://github.com/ryanfaircloth/tinyolly/commit/17f3b2b43cba70ff68df818ed67f2df538892d09))

## [0.2.0](https://github.com/ryanfaircloth/tinyolly/compare/helm-tinyolly-v0.1.1...helm-tinyolly-v0.2.0) (2026-01-14)

### ⚠ BREAKING CHANGES

- Release process now uses conventional commits and release-please
- Major folder restructure from scattered layout to organized monorepo

### Features

- add optional eBPF agent support to Helm chart ([8d6c9d4](https://github.com/ryanfaircloth/tinyolly/commit/8d6c9d41d787c3c9fb295d9ceb14942cfd547452))
- implement release-please for automated semantic versioning ([d5591e9](https://github.com/ryanfaircloth/tinyolly/commit/d5591e9c26d07d072cb589ccace52bdd705df13e))
- Migrate ai-agent demo to Helm with OTel operator auto-instrumentation ([9f93796](https://github.com/ryanfaircloth/tinyolly/commit/9f93796a5f9e926c3b5a89c588cef7fed95ab563))

### Code Refactoring

- restructure repository to standard monorepo layout ([1d0afcf](https://github.com/ryanfaircloth/tinyolly/commit/1d0afcf4f6ee8ebe2c921c4e96a65d56f5d9436d))
