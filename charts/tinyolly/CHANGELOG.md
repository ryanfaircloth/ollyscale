# Changelog

## [0.3.1](https://github.com/ryanfaircloth/tinyolly/compare/helm-tinyolly-v0.3.0...helm-tinyolly-v0.3.1) (2026-01-15)


### Features

* **ui:** refactor to separate static UI from FastAPI backend ([843b7a4](https://github.com/ryanfaircloth/tinyolly/commit/843b7a48c944af54e8de1cb2a6bff70d0837d83c))


### Code Refactoring

* **backend:** remove obsolete static and templates directories ([6c67eb7](https://github.com/ryanfaircloth/tinyolly/commit/6c67eb701bdc48ff37d7ca35b5369c1ee9ff2bb9))
* switch to local-only development builds ([d78ba92](https://github.com/ryanfaircloth/tinyolly/commit/d78ba920d14708572cdc4ee32c773c24eed2eefc))

## [0.3.0](https://github.com/ryanfaircloth/tinyolly/compare/helm-tinyolly-v0.2.2...helm-tinyolly-v0.3.0) (2026-01-14)


### ⚠ BREAKING CHANGES

* Release process now uses conventional commits and release-please
* Major folder restructure from scattered layout to organized monorepo

### Features

* add optional eBPF agent support to Helm chart ([8d6c9d4](https://github.com/ryanfaircloth/tinyolly/commit/8d6c9d41d787c3c9fb295d9ceb14942cfd547452))
* implement release-please for automated semantic versioning ([d5591e9](https://github.com/ryanfaircloth/tinyolly/commit/d5591e9c26d07d072cb589ccace52bdd705df13e))
* Migrate ai-agent demo to Helm with OTel operator auto-instrumentation ([9f93796](https://github.com/ryanfaircloth/tinyolly/commit/9f93796a5f9e926c3b5a89c588cef7fed95ab563))
* simplify local dev - make build creates tfvars ([78dfeb1](https://github.com/ryanfaircloth/tinyolly/commit/78dfeb1ac0f9a73ea7e0ceff8730c56c5e9af78b))


### Bug Fixes

* consolidate CI workflows and resolve all linting errors ([1ea8973](https://github.com/ryanfaircloth/tinyolly/commit/1ea8973de8c46c6eb8ff31b4aa91e3790f65a562))
* remove ai-agent-demo from build script + add noqa for telemetry ([17f3b2b](https://github.com/ryanfaircloth/tinyolly/commit/17f3b2b43cba70ff68df818ed67f2df538892d09))


### Code Refactoring

* restructure repository to standard monorepo layout ([1d0afcf](https://github.com/ryanfaircloth/tinyolly/commit/1d0afcf4f6ee8ebe2c921c4e96a65d56f5d9436d))
