# Changelog

## [0.1.3](https://github.com/ryanfaircloth/ollyscale/compare/demo-otel-agent-v0.1.2...demo-otel-agent-v0.1.3) (2026-01-20)


### Bug Fixes

* **demo-otel-agent:** update agent description for artifact rebuild ([fcfed94](https://github.com/ryanfaircloth/ollyscale/commit/fcfed9441000f5bab747f1925c32ad309518e883))
* **ollyscale-ui:** update package description for artifact rebuild ([fcfed94](https://github.com/ryanfaircloth/ollyscale/commit/fcfed9441000f5bab747f1925c32ad309518e883))

## [0.1.2](https://github.com/ryanfaircloth/ollyscale/compare/demo-otel-agent-v0.1.1...demo-otel-agent-v0.1.2) (2026-01-20)


### Documentation

* add component descriptions for artifact generation ([bcfba38](https://github.com/ryanfaircloth/ollyscale/commit/bcfba3885dc982e786cb60d0e3190aab24aee772))

## [0.1.1](https://github.com/ryanfaircloth/ollyscale/compare/demo-otel-agent-v0.1.0...demo-otel-agent-v0.1.1) (2026-01-19)


### Features

* **demo-otel-agent:** migrate to Poetry with multistage Docker build ([0ec14c0](https://github.com/ryanfaircloth/ollyscale/commit/0ec14c08653f15270161770e5ddd52d247763a29))
* migrate to semantic-release with multi-package support ([315ecb5](https://github.com/ryanfaircloth/ollyscale/commit/315ecb5a2c3a477fb6dd5e951a669fd20e161256))
* upgrade to modern semantic-release tooling ([d85e66c](https://github.com/ryanfaircloth/ollyscale/commit/d85e66c275833e76355376cfb47a3c50d2e93a09))


### Bug Fixes

* add glob cwd configuration to semantic-release-replace-plugin for correct path resolution ([40a32bc](https://github.com/ryanfaircloth/ollyscale/commit/40a32bc9da550c86e1175e6cfca04502ba85de28))
* **build:** ensure PEP 621 compliance in all pyproject.toml files ([327ebf4](https://github.com/ryanfaircloth/ollyscale/commit/327ebf492ac87c155c91d9da094baa1c7ec0b35c))
* **ci:** disable build step in semantic-release-pypi since we're not publishing to PyPI ([62a8f5a](https://github.com/ryanfaircloth/ollyscale/commit/62a8f5a1aac8857327a92427f8b286a4464a212d))
* **ci:** implement proper monorepo semantic-release with @qiwi/multi-semantic-release ([99cf15c](https://github.com/ryanfaircloth/ollyscale/commit/99cf15cb521c7ac09e649a7489d1335a857add16))
* **ci:** remove extend references to root pyproject.toml and add standalone release config ([d22a59a](https://github.com/ryanfaircloth/ollyscale/commit/d22a59a46f5b79dd0e91a53710a037123636ef10))
* **ci:** use @covage/semantic-release-poetry-plugin for Poetry version bumps ([682f425](https://github.com/ryanfaircloth/ollyscale/commit/682f425974e37b3a0fec5db62a8e2c5df99a8860))
* **ci:** use @semantic-release/exec with poetry version (semantic-release-poetry doesn't exist) ([ca57b0b](https://github.com/ryanfaircloth/ollyscale/commit/ca57b0b71749d9441c4930225b8e9b578cf3ac35))
* **ci:** use only semantic-release-replace-plugin for PEP 621 [project] version bumping ([1783844](https://github.com/ryanfaircloth/ollyscale/commit/178384456c7a6626961ceef7239f296294903468))
* **docker:** configure Poetry venv in-project for multi-stage builds ([fe79fa8](https://github.com/ryanfaircloth/ollyscale/commit/fe79fa869e8a80308a00f93cec99ba2fdd13e29b))
* **license:** standardize all projects to AGPL-3.0 ([86caffd](https://github.com/ryanfaircloth/ollyscale/commit/86caffdc0f02bd686db3b549413d1d086e59223f))
* **opamp-server:** reset version ([e7cdc38](https://github.com/ryanfaircloth/ollyscale/commit/e7cdc380dfd5b38a369847b16dc1af95a6eb58c9))
* **release:** add Docker plugin to demo-otel-agent and Docker credentials to workflow ([8de1c6e](https://github.com/ryanfaircloth/ollyscale/commit/8de1c6e5825bd3acc377184755b7df345f9d6074))
* **release:** set pypi srcDir to package root ([b97fa96](https://github.com/ryanfaircloth/ollyscale/commit/b97fa96eb9bf1ace2a979b231ec3f8271f3a3a11))
* **release:** set semantic-release-pypi srcDir per Python package and fix git assets paths\n\n- apps/ollyscale -&gt; srcDir apps/ollyscale\n- apps/demo -&gt; srcDir apps/demo\n- apps/demo-otel-agent -&gt; srcDir apps/demo-otel-agent\n- commit correct pyproject.toml per package ([a8b74b5](https://github.com/ryanfaircloth/ollyscale/commit/a8b74b566be262a26b3d4e2f198ad3d42235beb1))
* use full paths from repo root for semantic-release-replace-plugin file patterns ([fb3d7de](https://github.com/ryanfaircloth/ollyscale/commit/fb3d7de5f679324cd3e6387743c3f0e33483bb5e))

## 0.1.0 (2026-01-18)


### Features

* add README documentation for all release artifacts ([639133f](https://github.com/ryanfaircloth/ollyscale/commit/639133f94379e57b636efb0bc08fa2e3df1de156))

## 0.1.0 (2026-01-16)


### Bug Fixes

* **apps:** force rebuild of all containers after VERSION file removal ([e2b92fa](https://github.com/ryanfaircloth/ollyscale/commit/e2b92fa2279bc50ee6b7885c9930728a35d04225))
* consolidate CI workflows and resolve all linting errors ([79e53bf](https://github.com/ryanfaircloth/ollyscale/commit/79e53bf4220db6657922753e0dd3c7744806eeb9))
* remove ai-agent-demo from build script + add noqa for telemetry ([2156059](https://github.com/ryanfaircloth/ollyscale/commit/2156059608cf0ebbf7e0d0741cb356891a608a77))
* remove VERSION files entirely ([362fa38](https://github.com/ryanfaircloth/ollyscale/commit/362fa3831740bdeeb55db77bb4f2a262c2e26039))
* use manifest as single source of truth for versions ([a0a1241](https://github.com/ryanfaircloth/ollyscale/commit/a0a12416e553e93a9082e2870871392c39c5570d))


### Code Refactoring

* rename ai-agent-demo to demo-otel-agent ([eadefe6](https://github.com/ryanfaircloth/ollyscale/commit/eadefe689f6fe5433c4d6f56ce0d344df437b19b))
