# Changelog

## [0.1.1](https://github.com/ryanfaircloth/ollyscale/compare/api-v0.1.0...api-v0.1.1) (2026-02-08)


### Features

* implement graceful database migration coordination ([9cf2ee4](https://github.com/ryanfaircloth/ollyscale/commit/9cf2ee441666dd1e167d1c075ae4ff652640c3e9))
* **traces:** optimize search with batch query and lazy-load spans ([2d22a5f](https://github.com/ryanfaircloth/ollyscale/commit/2d22a5f338086113607ec6b863de126ccaf03636))


### Bug Fixes

* **storage:** remove unreachable dead code in get_service_map() ([4078be6](https://github.com/ryanfaircloth/ollyscale/commit/4078be6a8b5e4beca8e082536d8c55b531e80834))
* **tests:** increase timeouts for CI and slower machines ([3910af4](https://github.com/ryanfaircloth/ollyscale/commit/3910af43b4398ab73d5371064429cb8d6e12a360))


### Performance Improvements

* **build:** add comprehensive Podman build optimizations ([95e9f48](https://github.com/ryanfaircloth/ollyscale/commit/95e9f48a7b5c75abbd24d3e9f12df0942da5daa1))

## [0.1.0](https://github.com/ryanfaircloth/ollyscale/compare/api-v0.0.1...api-v0.1.0) (2026-02-04)


### ⚠ BREAKING CHANGES

* **storage:** migrate from Redis to PostgreSQL with comprehensive refactoring ([#111](https://github.com/ryanfaircloth/ollyscale/issues/111))

### Features

* **storage:** migrate from Redis to PostgreSQL with comprehensive refactoring ([#111](https://github.com/ryanfaircloth/ollyscale/issues/111)) ([99b93c9](https://github.com/ryanfaircloth/ollyscale/commit/99b93c9684ffb3764ffc809905086a480d9b5a52))
* **ui:** replace legacy UI with modern React-based web interface ([#113](https://github.com/ryanfaircloth/ollyscale/issues/113)) ([c570255](https://github.com/ryanfaircloth/ollyscale/commit/c570255b62e8ebd90de5d476f04b715f25627739))
