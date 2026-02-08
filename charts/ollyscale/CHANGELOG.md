# Changelog

## [0.2.1](https://github.com/ryanfaircloth/ollyscale/compare/chart-ollyscale-v0.2.0...chart-ollyscale-v0.2.1) (2026-02-08)


### Features

* **charts:** add pod annotation support to ollyscale-otel-agent deployments ([ee2e086](https://github.com/ryanfaircloth/ollyscale/commit/ee2e086a05733b9031557e466d7da0ac6e618e86))
* implement graceful database migration coordination ([9cf2ee4](https://github.com/ryanfaircloth/ollyscale/commit/9cf2ee441666dd1e167d1c075ae4ff652640c3e9))


### Bug Fixes

* **config:** enable gateway collector to receive telemetry data ([577f7ca](https://github.com/ryanfaircloth/ollyscale/commit/577f7caf2d7d1523f3a30ce6c43f5432828452b1))
* **db:** replica count ([5904734](https://github.com/ryanfaircloth/ollyscale/commit/5904734adc89b7b0be545f8f96e0fd500bced94c))
* **helm:** ensure migration ServiceAccount created before migration job ([75dc764](https://github.com/ryanfaircloth/ollyscale/commit/75dc764bc56d1389f8015532d98eea71fac4ddff))
* **helm:** remove hooks/waves from migration for parallel deployment ([fe8f0f7](https://github.com/ryanfaircloth/ollyscale/commit/fe8f0f717a7290622a27598e0e710c83a5dc0fb5))
* **ollyscale:** fix missing component labels ([77a4b7d](https://github.com/ryanfaircloth/ollyscale/commit/77a4b7d3b2e9d278f47cb1e550072297e9f437d3))
* route /v1/traces to browser-collector and add --remove-signatures to podman push ([ab33f6e](https://github.com/ryanfaircloth/ollyscale/commit/ab33f6e79b6fdb77f9d7c11bf3fe676693be2496))

## [0.2.0](https://github.com/ryanfaircloth/ollyscale/compare/chart-ollyscale-v0.1.10...chart-ollyscale-v0.2.0) (2026-02-04)


### ⚠ BREAKING CHANGES

* **storage:** migrate from Redis to PostgreSQL with comprehensive refactoring ([#111](https://github.com/ryanfaircloth/ollyscale/issues/111))

### Features

* **storage:** migrate from Redis to PostgreSQL with comprehensive refactoring ([#111](https://github.com/ryanfaircloth/ollyscale/issues/111)) ([99b93c9](https://github.com/ryanfaircloth/ollyscale/commit/99b93c9684ffb3764ffc809905086a480d9b5a52))
* **ui:** replace legacy UI with modern React-based web interface ([#113](https://github.com/ryanfaircloth/ollyscale/issues/113)) ([c570255](https://github.com/ryanfaircloth/ollyscale/commit/c570255b62e8ebd90de5d476f04b715f25627739))


### Bug Fixes

* resolve merge conflicts and precommit issues ([d13a198](https://github.com/ryanfaircloth/ollyscale/commit/d13a1980eb236191bd9319e8eca4fd0bf100d9c5))
* service map deduplication, dagre-d3 UI arrowhead bug, legend, and backend test ([1c535d6](https://github.com/ryanfaircloth/ollyscale/commit/1c535d685beb2dc1729701903a86bcc30a66fa38))

## [0.1.10](https://github.com/ryanfaircloth/ollyscale/compare/chart-ollyscale-v0.1.9...chart-ollyscale-v0.1.10) (2026-01-20)


### Features

* **build:** migrate apps/ollyscale from requirements.txt to Poetry ([2bbf7fd](https://github.com/ryanfaircloth/ollyscale/commit/2bbf7fdd267b0c4cf901de9e3dfe9db5146c29f6))
* migrate apps/demo to Poetry with modern pyproject.toml ([ab4cd98](https://github.com/ryanfaircloth/ollyscale/commit/ab4cd98ac96b14d309086993e439e751acc4acdc))
* migrate to semantic-release with multi-package support ([315ecb5](https://github.com/ryanfaircloth/ollyscale/commit/315ecb5a2c3a477fb6dd5e951a669fd20e161256))
* upgrade to modern semantic-release tooling ([d85e66c](https://github.com/ryanfaircloth/ollyscale/commit/d85e66c275833e76355376cfb47a3c50d2e93a09))


### Bug Fixes

* **ci:** correct initial version ([688587d](https://github.com/ryanfaircloth/ollyscale/commit/688587df76f70fc0d9295e06dab10f736057dd52))
* **ci:** minor revisions to config ([3192dfe](https://github.com/ryanfaircloth/ollyscale/commit/3192dfefddd67e6feacb43be23bfb1e456396b40))
* **helm-ollyscale:** trigger release ([79664ad](https://github.com/ryanfaircloth/ollyscale/commit/79664ad0325a10be57a4cb776edb662cf04c3017))

## [0.1.9](https://github.com/ryanfaircloth/ollyscale/compare/chart-ollyscale-v0.1.8...chart-ollyscale-v0.1.9) (2026-01-20)

## [0.1.8](https://github.com/ryanfaircloth/ollyscale/compare/chart-ollyscale-v0.1.7...chart-ollyscale-v0.1.8) (2026-01-20)

## [0.1.7](https://github.com/ryanfaircloth/ollyscale/compare/chart-ollyscale-v0.1.6...chart-ollyscale-v0.1.7) (2026-01-20)

## [0.1.6](https://github.com/ryanfaircloth/ollyscale/compare/chart-ollyscale-v0.1.5...chart-ollyscale-v0.1.6) (2026-01-20)

## [0.1.5](https://github.com/ryanfaircloth/ollyscale/compare/chart-ollyscale-v0.1.4...chart-ollyscale-v0.1.5) (2026-01-20)

## [0.1.4](https://github.com/ryanfaircloth/ollyscale/compare/chart-ollyscale-v0.1.3...chart-ollyscale-v0.1.4) (2026-01-20)

## [0.1.3](https://github.com/ryanfaircloth/ollyscale/compare/chart-ollyscale-v0.1.2...chart-ollyscale-v0.1.3) (2026-01-20)

## [0.1.2](https://github.com/ryanfaircloth/ollyscale/compare/chart-ollyscale-v0.1.1...chart-ollyscale-v0.1.2) (2026-01-20)

## [0.1.1](https://github.com/ryanfaircloth/ollyscale/compare/chart-ollyscale-v0.1.0...chart-ollyscale-v0.1.1) (2026-01-19)


### Features

* **build:** migrate apps/ollyscale from requirements.txt to Poetry ([2bbf7fd](https://github.com/ryanfaircloth/ollyscale/commit/2bbf7fdd267b0c4cf901de9e3dfe9db5146c29f6))
* migrate apps/demo to Poetry with modern pyproject.toml ([ab4cd98](https://github.com/ryanfaircloth/ollyscale/commit/ab4cd98ac96b14d309086993e439e751acc4acdc))
* migrate to semantic-release with multi-package support ([315ecb5](https://github.com/ryanfaircloth/ollyscale/commit/315ecb5a2c3a477fb6dd5e951a669fd20e161256))
* upgrade to modern semantic-release tooling ([d85e66c](https://github.com/ryanfaircloth/ollyscale/commit/d85e66c275833e76355376cfb47a3c50d2e93a09))


### Bug Fixes

* **ci:** correct initial version ([688587d](https://github.com/ryanfaircloth/ollyscale/commit/688587df76f70fc0d9295e06dab10f736057dd52))
* **ci:** minor revisions to config ([3192dfe](https://github.com/ryanfaircloth/ollyscale/commit/3192dfefddd67e6feacb43be23bfb1e456396b40))
* **helm-ollyscale:** trigger release ([79664ad](https://github.com/ryanfaircloth/ollyscale/commit/79664ad0325a10be57a4cb776edb662cf04c3017))
