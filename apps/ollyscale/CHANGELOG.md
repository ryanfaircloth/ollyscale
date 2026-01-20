# Changelog

## [2.3.1](https://github.com/ryanfaircloth/ollyscale/compare/ollyscale-v2.3.0...ollyscale-v2.3.1) (2026-01-20)


### Documentation

* **ollyscale:** improve module docstring for clarity ([130202d](https://github.com/ryanfaircloth/ollyscale/commit/130202d9c4d1e4267ff0cd2d9db3b88e1eee24cb))

## [2.3.0](https://github.com/ryanfaircloth/ollyscale/compare/ollyscale-v2.2.0...ollyscale-v2.3.0) (2026-01-19)


### Features

* **build:** migrate apps/ollyscale from requirements.txt to Poetry ([2bbf7fd](https://github.com/ryanfaircloth/ollyscale/commit/2bbf7fdd267b0c4cf901de9e3dfe9db5146c29f6))
* migrate to semantic-release with multi-package support ([315ecb5](https://github.com/ryanfaircloth/ollyscale/commit/315ecb5a2c3a477fb6dd5e951a669fd20e161256))
* upgrade to modern semantic-release tooling ([d85e66c](https://github.com/ryanfaircloth/ollyscale/commit/d85e66c275833e76355376cfb47a3c50d2e93a09))


### Bug Fixes

* add glob cwd configuration to semantic-release-replace-plugin for correct path resolution ([40a32bc](https://github.com/ryanfaircloth/ollyscale/commit/40a32bc9da550c86e1175e6cfca04502ba85de28))
* add Poetry test dependency group ([d5bfd2d](https://github.com/ryanfaircloth/ollyscale/commit/d5bfd2d5eaa0fc53b14dd8b1da4a446aa60c58c0))
* **build:** ensure PEP 621 compliance in all pyproject.toml files ([327ebf4](https://github.com/ryanfaircloth/ollyscale/commit/327ebf492ac87c155c91d9da094baa1c7ec0b35c))
* **ci:** disable build step in semantic-release-pypi since we're not publishing to PyPI ([62a8f5a](https://github.com/ryanfaircloth/ollyscale/commit/62a8f5a1aac8857327a92427f8b286a4464a212d))
* **ci:** implement proper monorepo semantic-release with @qiwi/multi-semantic-release ([99cf15c](https://github.com/ryanfaircloth/ollyscale/commit/99cf15cb521c7ac09e649a7489d1335a857add16))
* **ci:** remove extend references to root pyproject.toml and add standalone release config ([d22a59a](https://github.com/ryanfaircloth/ollyscale/commit/d22a59a46f5b79dd0e91a53710a037123636ef10))
* **ci:** use @covage/semantic-release-poetry-plugin for Poetry version bumps ([682f425](https://github.com/ryanfaircloth/ollyscale/commit/682f425974e37b3a0fec5db62a8e2c5df99a8860))
* **ci:** use @semantic-release/exec with poetry version (semantic-release-poetry doesn't exist) ([ca57b0b](https://github.com/ryanfaircloth/ollyscale/commit/ca57b0b71749d9441c4930225b8e9b578cf3ac35))
* **ci:** use only semantic-release-replace-plugin for PEP 621 [project] version bumping ([1783844](https://github.com/ryanfaircloth/ollyscale/commit/178384456c7a6626961ceef7239f296294903468))
* **license:** standardize all projects to AGPL-3.0 ([86caffd](https://github.com/ryanfaircloth/ollyscale/commit/86caffdc0f02bd686db3b549413d1d086e59223f))
* **ollyscale:** missing file ([2d9c4d0](https://github.com/ryanfaircloth/ollyscale/commit/2d9c4d0e134cd2b0f73daf3febd17d22c990f17b))
* **ollyscale:** trigger release ([cb0b852](https://github.com/ryanfaircloth/ollyscale/commit/cb0b852f816653fbfc877f24b21947289c31ecc8))
* **release:** set pypi srcDir to package root ([b97fa96](https://github.com/ryanfaircloth/ollyscale/commit/b97fa96eb9bf1ace2a979b231ec3f8271f3a3a11))
* **release:** set semantic-release-pypi srcDir per Python package and fix git assets paths\n\n- apps/ollyscale -&gt; srcDir apps/ollyscale\n- apps/demo -&gt; srcDir apps/demo\n- apps/demo-otel-agent -&gt; srcDir apps/demo-otel-agent\n- commit correct pyproject.toml per package ([a8b74b5](https://github.com/ryanfaircloth/ollyscale/commit/a8b74b566be262a26b3d4e2f198ad3d42235beb1))
* resolve pre-commit issues ([f9531a9](https://github.com/ryanfaircloth/ollyscale/commit/f9531a9e4958588c0f3d5a75a5d9999169f4ecf8))
* use full paths from repo root for semantic-release-replace-plugin file patterns ([fb3d7de](https://github.com/ryanfaircloth/ollyscale/commit/fb3d7de5f679324cd3e6387743c3f0e33483bb5e))

## [2.2.0](https://github.com/ryanfaircloth/ollyscale/compare/ollyscale-v2.1.9...ollyscale-v2.2.0) (2026-01-18)


### Features

* **ollyscale:** add README and update bootstrap-sha for testing ([ebc5cd8](https://github.com/ryanfaircloth/ollyscale/commit/ebc5cd8fae9a02c8e64071a33172367e1b12d53c))
