# Changelog

## [32.1.0](https://github.com/ryanfaircloth/tinyolly/compare/v32.0.0...v32.1.0) (2026-01-15)


### Features

* **ui:** refactor to separate static UI from FastAPI backend ([843b7a4](https://github.com/ryanfaircloth/tinyolly/commit/843b7a48c944af54e8de1cb2a6bff70d0837d83c))


### Bug Fixes

* add shellcheck disable comment for terraform variable check ([9565356](https://github.com/ryanfaircloth/tinyolly/commit/9565356e3571c8128667f88a1999682082c9eb28))
* disable ruff TCH rules conflicting with FastAPI dependency injection ([d7f3626](https://github.com/ryanfaircloth/tinyolly/commit/d7f36266d690b450e19f7a55255e49cc3d923d6e))
* **k8s:** use release-please manifest versions in terraform ([94b17ac](https://github.com/ryanfaircloth/tinyolly/commit/94b17ac0fe88e3c606d4af257ffed3f811df0265))
* **ui:** restore missing HTML structure in index.html ([e6a341f](https://github.com/ryanfaircloth/tinyolly/commit/e6a341f49193bc098b4d90f241b142363d45bba8))
* **ui:** update Vite to 6.4.1 to resolve esbuild security vulnerability ([5af2222](https://github.com/ryanfaircloth/tinyolly/commit/5af2222436bac03e41ab8b8a181cc259b1f88b6a))


### Documentation

* add critical rule against bypassing pre-commit checks ([ab8ff24](https://github.com/ryanfaircloth/tinyolly/commit/ab8ff2458d5ba342fe9ec94d7ac93736149e94cb))


### Code Refactoring

* **backend:** remove obsolete static and templates directories ([6c67eb7](https://github.com/ryanfaircloth/tinyolly/commit/6c67eb701bdc48ff37d7ca35b5369c1ee9ff2bb9))
* switch to local-only development builds ([d78ba92](https://github.com/ryanfaircloth/tinyolly/commit/d78ba920d14708572cdc4ee32c773c24eed2eefc))

## [32.0.0](https://github.com/ryanfaircloth/tinyolly/compare/v31.1.4...v32.0.0) (2026-01-14)


### ⚠ BREAKING CHANGES

* Bump all versions to force new release
* Release process now uses conventional commits and release-please
* Major folder restructure from scattered layout to organized monorepo

### Features

* Add ArgoCD bootstrap pattern with Gateway HTTPRoute ([c683471](https://github.com/ryanfaircloth/tinyolly/commit/c6834713f6d8555c493a6ac5ee6647c88e0387b1))
* add optional eBPF agent support to Helm chart ([8d6c9d4](https://github.com/ryanfaircloth/tinyolly/commit/8d6c9d41d787c3c9fb295d9ceb14942cfd547452))
* add workflow to build containers on tag push ([7fa883d](https://github.com/ryanfaircloth/tinyolly/commit/7fa883dd3c8e9a556bc3961066f9afb29f413344))
* add workflow_dispatch trigger to build-release workflow ([df7247a](https://github.com/ryanfaircloth/tinyolly/commit/df7247aab6690d0e7fe2e97ee4e33a038e611cc3))
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
* simplify local dev - make build creates tfvars ([78dfeb1](https://github.com/ryanfaircloth/tinyolly/commit/78dfeb1ac0f9a73ea7e0ceff8730c56c5e9af78b))
* switch from flux to argocd ([de9eabd](https://github.com/ryanfaircloth/tinyolly/commit/de9eabd93b653d17ce5f917d0e6f46bacd116952))
* use appprojects and move hard coded values to variables ([be08faf](https://github.com/ryanfaircloth/tinyolly/commit/be08fafbcf1945451a0c84d12adb0481588d3edc))


### Bug Fixes

* apm filter issues with redis ([0d2ee9c](https://github.com/ryanfaircloth/tinyolly/commit/0d2ee9c4bf07a995a44a2e5214ac545376db803e))
* APM map for hide mode ([ca6c177](https://github.com/ryanfaircloth/tinyolly/commit/ca6c177ee750e15382f705da127ff0208696ca07))
* **apps:** force rebuild of all containers after VERSION file removal ([d21b4f7](https://github.com/ryanfaircloth/tinyolly/commit/d21b4f7eb6eca71c36cd245e915688737fc47781))
* build progress ([de96dc0](https://github.com/ryanfaircloth/tinyolly/commit/de96dc06f37061a877e89791886583f5707ef356))
* **ci:** add root package to track CI/infrastructure changes ([0e4be44](https://github.com/ryanfaircloth/tinyolly/commit/0e4be44a6982b6f91f67e27b8bf9ec750308b615))
* **ci:** correct GHCR paths and remove duplicate ArgoCD update job ([da5e69b](https://github.com/ryanfaircloth/tinyolly/commit/da5e69b9c2cdcb4424027aaf169da6559fc05340))
* **ci:** correct JSON syntax in release-please config ([1038817](https://github.com/ryanfaircloth/tinyolly/commit/10388177797d6afe9624e07d54f3c08cff183c04))
* **ci:** ensure release-please updates ArgoCD manifests correctly ([701026e](https://github.com/ryanfaircloth/tinyolly/commit/701026e1561182385657cc04f5d476b0c85c2dcc))
* **ci:** remove old release script ([ff3d3b0](https://github.com/ryanfaircloth/tinyolly/commit/ff3d3b08a06b2e5f57dfc90bdbb02547e3081a9a))
* **ci:** use repo-root relative paths in release-please config ([6bf658d](https://github.com/ryanfaircloth/tinyolly/commit/6bf658d6d995cdf868996d92eba7baf6a9d95d05))
* consolidate CI workflows and resolve all linting errors ([1ea8973](https://github.com/ryanfaircloth/tinyolly/commit/1ea8973de8c46c6eb8ff31b4aa91e3790f65a562))
* consolidate collectors ([4769bd0](https://github.com/ryanfaircloth/tinyolly/commit/4769bd0a6265221a8b553a7de27198fa3c236412))
* correct container registry paths for demo images ([c03de9f](https://github.com/ryanfaircloth/tinyolly/commit/c03de9f2af80d0526f0dd8a9c987ecb386557f8e))
* correct fixture name reference in tests ([2c540b7](https://github.com/ryanfaircloth/tinyolly/commit/2c540b70d58849e89f7747270cb3fde173c82958))
* **deps:** update opamp-server go dependencies ([2ad7b04](https://github.com/ryanfaircloth/tinyolly/commit/2ad7b048002603d6edd355de701d2244b5808a8e))
* **deps:** update opamp-server go dependencies ([00cde8f](https://github.com/ryanfaircloth/tinyolly/commit/00cde8f4c3c30ecaae767e0b5fea5025a6074576))
* disable kafka-ui for now ([5217447](https://github.com/ryanfaircloth/tinyolly/commit/5217447d561eec957c95d46ca657cc8719cae626))
* exclude CHANGELOG.md from markdownlint ([190ccce](https://github.com/ryanfaircloth/tinyolly/commit/190cccef98f45e2c76f62ee8247bef8456402c4c))
* explicitly disable CHANGELOG generation with changelog: false ([ec3fa7a](https://github.com/ryanfaircloth/tinyolly/commit/ec3fa7a7affe488018ba9f4006c02cf57bd564dc))
* force version bumps to bypass untagged PR issue ([1561111](https://github.com/ryanfaircloth/tinyolly/commit/1561111d49191e7dab84b340d9decf31c97144e2))
* improve hideing our own data ([0c19db4](https://github.com/ryanfaircloth/tinyolly/commit/0c19db4a3e88eaaa4a557fd87411a1367a7e4dc0))
* improve metrics filter when only TO is a contributor ([64f3f27](https://github.com/ryanfaircloth/tinyolly/commit/64f3f274a2ea2d4eee2e209bc254ea24a411d46b))
* limits ([04b4a45](https://github.com/ryanfaircloth/tinyolly/commit/04b4a45f0c14498441e326f007d9159e388df26d))
* **opamp:** correct Go syntax and Dockerfile ([8eeaba4](https://github.com/ryanfaircloth/tinyolly/commit/8eeaba4afa53e748e5a350028c3e10a1b2cb6dce))
* otel for olly route ([a29758c](https://github.com/ryanfaircloth/tinyolly/commit/a29758c1278e21ba89d0ab543740bba85f291967))
* prevent CHANGELOG.md lint failures ([7170e34](https://github.com/ryanfaircloth/tinyolly/commit/7170e347981b10f046beae44ad74be289bd473d4))
* prevent CHANGELOG.md lint failures ([0d0e761](https://github.com/ryanfaircloth/tinyolly/commit/0d0e761a128ba5de80e4bc80714118a1bfaafd8c))
* reduce complexity of build process ([6592f47](https://github.com/ryanfaircloth/tinyolly/commit/6592f475857482bb26f10345b5d107db19b5b689))
* remove ai-agent-demo from build script + add noqa for telemetry ([17f3b2b](https://github.com/ryanfaircloth/tinyolly/commit/17f3b2b43cba70ff68df818ed67f2df538892d09))
* remove changelog: false to enable GitHub release notes ([10960b8](https://github.com/ryanfaircloth/tinyolly/commit/10960b881d24da168d3317def183944e37472595))
* remove VERSION files entirely ([b3856ae](https://github.com/ryanfaircloth/tinyolly/commit/b3856aebc2baa3758c0278a00d3f567acac8e388))
* rendering when unhiding ([4473ed8](https://github.com/ryanfaircloth/tinyolly/commit/4473ed87397b3ce4b19424bea10b4412e8601d62))
* simplify tag patterns for workflow triggers ([0f60ced](https://github.com/ryanfaircloth/tinyolly/commit/0f60ced88b434d588b0027eb196139a992029f71))
* use --push for multi-platform Docker builds in CI ([a905ebf](https://github.com/ryanfaircloth/tinyolly/commit/a905ebf8517ecff9ff00beef8223fe0c993bb534))
* use correct GHCR registry path in Dockerfiles ([4f6b5c9](https://github.com/ryanfaircloth/tinyolly/commit/4f6b5c9cf06a1fa9076e3583b7884a327ac0b09a))
* use manifest as single source of truth for versions ([e9f9530](https://github.com/ryanfaircloth/tinyolly/commit/e9f95302a2e26a5409caedf79165a35d384cecf3))
* use proper registry hierarchy structure ([e7670dc](https://github.com/ryanfaircloth/tinyolly/commit/e7670dca82c898b0705fb531cbb7ca939348cc28))


### Documentation

* move build system docs and update paths ([67bec86](https://github.com/ryanfaircloth/tinyolly/commit/67bec8651d478fc59f6ddc9ff8c8a052d38640c3))


### Code Refactoring

* **ci:** let release-please handle ArgoCD version updates ([7cc4393](https://github.com/ryanfaircloth/tinyolly/commit/7cc43934bf0f59fddbb643be870b6dd45db95c83))
* consolidate build workflows into release-please.yml ([b994736](https://github.com/ryanfaircloth/tinyolly/commit/b994736f16d94c5cfaae6d0625e345eb6ae5e42d))
* rename ai-agent-demo to demo-otel-agent ([eadefe6](https://github.com/ryanfaircloth/tinyolly/commit/eadefe689f6fe5433c4d6f56ce0d344df437b19b))
* restructure repository to standard monorepo layout ([1d0afcf](https://github.com/ryanfaircloth/tinyolly/commit/1d0afcf4f6ee8ebe2c921c4e96a65d56f5d9436d))
* Split demos into separate Helm charts and ArgoCD applications ([0a7863a](https://github.com/ryanfaircloth/tinyolly/commit/0a7863a411f8659457e9845042840224b5655609))

## [31.1.3](https://github.com/ryanfaircloth/tinyolly/compare/v31.1.2...v31.1.3) (2026-01-14)


### Bug Fixes

* exclude CHANGELOG.md from markdownlint ([190ccce](https://github.com/ryanfaircloth/tinyolly/commit/190cccef98f45e2c76f62ee8247bef8456402c4c))
* prevent CHANGELOG.md lint failures ([7170e34](https://github.com/ryanfaircloth/tinyolly/commit/7170e347981b10f046beae44ad74be289bd473d4))
* prevent CHANGELOG.md lint failures ([0d0e761](https://github.com/ryanfaircloth/tinyolly/commit/0d0e761a128ba5de80e4bc80714118a1bfaafd8c))

## [31.1.2](https://github.com/ryanfaircloth/tinyolly/compare/v31.1.1...v31.1.2) (2026-01-14)


### Bug Fixes

* remove changelog: false to enable GitHub release notes ([10960b8](https://github.com/ryanfaircloth/tinyolly/commit/10960b881d24da168d3317def183944e37472595))
