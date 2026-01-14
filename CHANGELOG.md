# Changelog

## [31.0.2](https://github.com/ryanfaircloth/tinyolly/compare/v31.0.1...v31.0.2) (2026-01-14)


### Bug Fixes

* **ci:** correct GHCR paths and remove duplicate ArgoCD update job ([da5e69b](https://github.com/ryanfaircloth/tinyolly/commit/da5e69b9c2cdcb4424027aaf169da6559fc05340))

## [31.0.1](https://github.com/ryanfaircloth/tinyolly/compare/v31.0.0...v31.0.1) (2026-01-14)


### Bug Fixes

* **opamp:** correct Go syntax and Dockerfile ([8eeaba4](https://github.com/ryanfaircloth/tinyolly/commit/8eeaba4afa53e748e5a350028c3e10a1b2cb6dce))

## [31.0.0](https://github.com/ryanfaircloth/tinyolly/compare/v30.0.1...v31.0.0) (2026-01-14)


### ⚠ BREAKING CHANGES

* Release process now uses conventional commits and release-please
* Major folder restructure from scattered layout to organized monorepo

### Features

* Add ArgoCD bootstrap pattern with Gateway HTTPRoute ([c683471](https://github.com/ryanfaircloth/tinyolly/commit/c6834713f6d8555c493a6ac5ee6647c88e0387b1))
* add optional eBPF agent support to Helm chart ([8d6c9d4](https://github.com/ryanfaircloth/tinyolly/commit/8d6c9d41d787c3c9fb295d9ceb14942cfd547452))
* argocd is accessible ([62b8dcd](https://github.com/ryanfaircloth/tinyolly/commit/62b8dcda9e84c5af06b74058e2b6ae51cf238473))
* base cluster ([92d4ed6](https://github.com/ryanfaircloth/tinyolly/commit/92d4ed6f5185d38d3aa05ba2163cdfc4b2ed1cc8))
* build and push works ([7fdfe32](https://github.com/ryanfaircloth/tinyolly/commit/7fdfe326d16ef7c8590500416159e74a72e604fe))
* cache busting ([d6c1a11](https://github.com/ryanfaircloth/tinyolly/commit/d6c1a11799848ee29e7b788e512a8d40f3d373aa))
* **ci:** update ArgoCD applications on release ([8d7cf83](https://github.com/ryanfaircloth/tinyolly/commit/8d7cf835d3bd3d5079a72af0ab53111fa46a743e))
* cleanup ([3491064](https://github.com/ryanfaircloth/tinyolly/commit/34910649f5775df857105163c1051f59233e844c))
* consolidation of resources ([8741198](https://github.com/ryanfaircloth/tinyolly/commit/87411980c4affb8d2dcf2ac9776606030ef0cb0a))
* hide to data by default ([c8cb7c5](https://github.com/ryanfaircloth/tinyolly/commit/c8cb7c53156c890177b9483ad7140f46bfa50972))
* implement release-please for automated semantic versioning ([d5591e9](https://github.com/ryanfaircloth/tinyolly/commit/d5591e9c26d07d072cb589ccace52bdd705df13e))
* Migrate ai-agent demo to Helm with OTel operator auto-instrumentation ([9f93796](https://github.com/ryanfaircloth/tinyolly/commit/9f93796a5f9e926c3b5a89c588cef7fed95ab563))
* migrate to instrumentation ([76fbd9e](https://github.com/ryanfaircloth/tinyolly/commit/76fbd9ea0c755eb68fdcecbc1b6f898ee8484711))
* redit for tinyolly ([400103b](https://github.com/ryanfaircloth/tinyolly/commit/400103bce490eafe688d1bbd8fea3ea955ec5e3f))
* runtime updates ([4647330](https://github.com/ryanfaircloth/tinyolly/commit/464733049ccc58066fa2d2b6280130e44e504626))
* switch from flux to argocd ([de9eabd](https://github.com/ryanfaircloth/tinyolly/commit/de9eabd93b653d17ce5f917d0e6f46bacd116952))
* use appprojects and move hard coded values to variables ([be08faf](https://github.com/ryanfaircloth/tinyolly/commit/be08fafbcf1945451a0c84d12adb0481588d3edc))


### Bug Fixes

* apm filter issues with redis ([0d2ee9c](https://github.com/ryanfaircloth/tinyolly/commit/0d2ee9c4bf07a995a44a2e5214ac545376db803e))
* APM map for hide mode ([ca6c177](https://github.com/ryanfaircloth/tinyolly/commit/ca6c177ee750e15382f705da127ff0208696ca07))
* build progress ([de96dc0](https://github.com/ryanfaircloth/tinyolly/commit/de96dc06f37061a877e89791886583f5707ef356))
* **ci:** add root package to track CI/infrastructure changes ([0e4be44](https://github.com/ryanfaircloth/tinyolly/commit/0e4be44a6982b6f91f67e27b8bf9ec750308b615))
* **ci:** correct JSON syntax in release-please config ([1038817](https://github.com/ryanfaircloth/tinyolly/commit/10388177797d6afe9624e07d54f3c08cff183c04))
* **ci:** ensure release-please updates ArgoCD manifests correctly ([701026e](https://github.com/ryanfaircloth/tinyolly/commit/701026e1561182385657cc04f5d476b0c85c2dcc))
* **ci:** use repo-root relative paths in release-please config ([6bf658d](https://github.com/ryanfaircloth/tinyolly/commit/6bf658d6d995cdf868996d92eba7baf6a9d95d05))
* consolidate collectors ([4769bd0](https://github.com/ryanfaircloth/tinyolly/commit/4769bd0a6265221a8b553a7de27198fa3c236412))
* **deps:** update opamp-server go dependencies ([2ad7b04](https://github.com/ryanfaircloth/tinyolly/commit/2ad7b048002603d6edd355de701d2244b5808a8e))
* **deps:** update opamp-server go dependencies ([00cde8f](https://github.com/ryanfaircloth/tinyolly/commit/00cde8f4c3c30ecaae767e0b5fea5025a6074576))
* disable kafka-ui for now ([5217447](https://github.com/ryanfaircloth/tinyolly/commit/5217447d561eec957c95d46ca657cc8719cae626))
* improve hideing our own data ([0c19db4](https://github.com/ryanfaircloth/tinyolly/commit/0c19db4a3e88eaaa4a557fd87411a1367a7e4dc0))
* improve metrics filter when only TO is a contributor ([64f3f27](https://github.com/ryanfaircloth/tinyolly/commit/64f3f274a2ea2d4eee2e209bc254ea24a411d46b))
* limits ([04b4a45](https://github.com/ryanfaircloth/tinyolly/commit/04b4a45f0c14498441e326f007d9159e388df26d))
* otel for olly route ([a29758c](https://github.com/ryanfaircloth/tinyolly/commit/a29758c1278e21ba89d0ab543740bba85f291967))
* reduce complexity of build process ([6592f47](https://github.com/ryanfaircloth/tinyolly/commit/6592f475857482bb26f10345b5d107db19b5b689))
* rendering when unhiding ([4473ed8](https://github.com/ryanfaircloth/tinyolly/commit/4473ed87397b3ce4b19424bea10b4412e8601d62))
* use --push for multi-platform Docker builds in CI ([a905ebf](https://github.com/ryanfaircloth/tinyolly/commit/a905ebf8517ecff9ff00beef8223fe0c993bb534))
* use correct GHCR registry path in Dockerfiles ([4f6b5c9](https://github.com/ryanfaircloth/tinyolly/commit/4f6b5c9cf06a1fa9076e3583b7884a327ac0b09a))


### Documentation

* move build system docs and update paths ([67bec86](https://github.com/ryanfaircloth/tinyolly/commit/67bec8651d478fc59f6ddc9ff8c8a052d38640c3))


### Code Refactoring

* **ci:** let release-please handle ArgoCD version updates ([7cc4393](https://github.com/ryanfaircloth/tinyolly/commit/7cc43934bf0f59fddbb643be870b6dd45db95c83))
* rename ai-agent-demo to demo-otel-agent ([eadefe6](https://github.com/ryanfaircloth/tinyolly/commit/eadefe689f6fe5433c4d6f56ce0d344df437b19b))
* restructure repository to standard monorepo layout ([1d0afcf](https://github.com/ryanfaircloth/tinyolly/commit/1d0afcf4f6ee8ebe2c921c4e96a65d56f5d9436d))
* Split demos into separate Helm charts and ArgoCD applications ([0a7863a](https://github.com/ryanfaircloth/tinyolly/commit/0a7863a411f8659457e9845042840224b5655609))
