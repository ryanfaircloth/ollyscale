# Changelog

## 1.0.0 (2026-01-16)


### ⚠ BREAKING CHANGES

* Release process now uses conventional commits and release-please
* Major folder restructure from scattered layout to organized monorepo

### Features

* implement release-please for automated semantic versioning ([d5591e9](https://github.com/ryanfaircloth/ollyscale/commit/d5591e9c26d07d072cb589ccace52bdd705df13e))


### Bug Fixes

* **apps:** force rebuild of all containers after VERSION file removal ([e2b92fa](https://github.com/ryanfaircloth/ollyscale/commit/e2b92fa2279bc50ee6b7885c9930728a35d04225))
* **opamp:** correct Go syntax and Dockerfile ([75910d3](https://github.com/ryanfaircloth/ollyscale/commit/75910d3daf7ee39a1f75e833b738f43ff7dbaa2c))
* remove ai-agent-demo from build script + add noqa for telemetry ([2156059](https://github.com/ryanfaircloth/ollyscale/commit/2156059608cf0ebbf7e0d0741cb356891a608a77))
* remove VERSION files entirely ([362fa38](https://github.com/ryanfaircloth/ollyscale/commit/362fa3831740bdeeb55db77bb4f2a262c2e26039))
* use manifest as single source of truth for versions ([a0a1241](https://github.com/ryanfaircloth/ollyscale/commit/a0a12416e553e93a9082e2870871392c39c5570d))


### Code Refactoring

* restructure repository to standard monorepo layout ([1d0afcf](https://github.com/ryanfaircloth/ollyscale/commit/1d0afcf4f6ee8ebe2c921c4e96a65d56f5d9436d))
