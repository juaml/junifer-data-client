# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/), and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

This project uses [*towncrier*](https://towncrier.readthedocs.io/) and the changes for the upcoming release can be found in <https://github.com/juaml/junifer-data-client/tree/main/changelog.d/>.

<!-- towncrier release notes start -->

## [1.5.0](https://github.com/juaml/junifer-data-client/tree/1.5.0) - 2026-10-07

### Added

- Support Python 3.14 ([#13](https://github.com/juaml/junifer-data-client/issues/13))

### Changed

- Make repeated `get` calls much faster by checking each tagged dataset only once per process and skipping `datalad get` for files whose content is already present ([#13](https://github.com/juaml/junifer-data-client/issues/13))

### Fixed

- Remove the retired GIN remote from junifer-data installations ([#13](https://github.com/juaml/junifer-data-client/issues/13))


## [1.4.0](https://github.com/juaml/junifer-data-client/tree/1.4.0) - 2026-10-05

### Added

- Add unit tests and CI workflow ([#4](https://github.com/juaml/junifer-data-client/issues/4))

### Changed

- Fetch junifer-data from cerebra.fz-juelich.de instead of GitHub and migrate existing installations ([#5](https://github.com/juaml/junifer-data-client/issues/5))


## [1.3.0](https://github.com/juaml/junifer-data-client/tree/1.3.0) - 2025-03-21

### Added

- Allow `junifer-data` to be accessed via `junifer` CLI ([#5](https://github.com/juaml/junifer-data-client/issues/5))


## [1.2.0](https://github.com/juaml/junifer-data-client/tree/1.2.0) - 2025-03-06

### Added

- Add `hexsha` parameter for get operation via API and CLI and for `check_dataset` ([#3](https://github.com/juaml/junifer-data-client/issues/3))

### Changed

- Check commit hash instead of checking out state if dataset is installed ([#3](https://github.com/juaml/junifer-data-client/issues/3))


## [1.1.0](https://github.com/juaml/junifer-data-client/tree/1.1.0) - 2025-02-10

### Added

- Add `download` command to CLI ([#1](https://github.com/juaml/junifer-data-client/issues/1))


## [1.0.0](https://github.com/juaml/junifer-data-client/tree/1.0.0) - 2025-01-18

### Added

- Create repository and set up initial implementation
