# Changelog

## [1.2.1](https://github.com/cauethenorio/edne-correios-loader/compare/v1.2.0...v1.2.1) (2026-11-09)


### Documentation

* normalize changelog to release-please's format ([#19](https://github.com/cauethenorio/edne-correios-loader/issues/19)) ([cc0af7c](https://github.com/cauethenorio/edne-correios-loader/commit/cc0af7c935e9dfc7b6417d5b1dfda59b49052d31))
* split intro paragraph for readability ([7df349c](https://github.com/cauethenorio/edne-correios-loader/commit/7df349c3d33c3084888ef829bce2cc56035cdbe1))

## [1.2.0](https://github.com/cauethenorio/edne-correios-loader/compare/1.1.0...v1.2.0) (2026-03-05)


### Features

* Allow custom table names via dict or callable ([#14](https://github.com/cauethenorio/edne-correios-loader/issues/14))

## [1.1.0](https://github.com/cauethenorio/edne-correios-loader/compare/1.0.0...1.1.0) (2026-02-11)


### Bug Fixes

* Attempt to fix temporary file handling on Windows (WinError 32) ([#4](https://github.com/cauethenorio/edne-correios-loader/issues/4))
* Fix vulnerability: Bumped cryptography from 46.0.4 to 46.0.5

## [1.0.0](https://github.com/cauethenorio/edne-correios-loader/compare/0.2.0...1.0.0) (2026-02-10)


### ⚠ BREAKING CHANGES

* Dropped Python 3.8 and 3.9 support, which reached EOL

### Features

* Added Python 3.14 support

### Bug Fixes

* Fixed compatibility with Click 8.2+

### Documentation

* Added instructions on how to use it with uvx

### Build System

* Migrated tooling from hatch to uv

## [0.2.0](https://github.com/cauethenorio/edne-correios-loader/compare/0.1.3...0.2.0) (2025-02-23)


### Features

* Added compatibility with python 3.13

### Bug Fixes

* Updated db writer to skip CEPs without municipality IBGE code when populating cep_unificado

## [0.1.3](https://github.com/cauethenorio/edne-correios-loader/compare/0.1.2...0.1.3) (2024-06-03)


### Bug Fixes

* Fixed incompatibility with MS SQL Server ([#3](https://github.com/cauethenorio/edne-correios-loader/issues/3))

### Miscellaneous Chores

* Replaced Black with Ruff for code formatting

## [0.1.2](https://github.com/cauethenorio/edne-correios-loader/compare/0.1.1...0.1.2) (2023-10-11)


### Features

* Added compatibility with python 3.8

## [0.1.1](https://github.com/cauethenorio/edne-correios-loader/compare/0.1.0...0.1.1) (2023-10-06)


### Features

* Added extras for MySQL and PostgreSQL driver installation

### Documentation

* Improved README and added english version

## 0.1.0 (2023-10-06)


### Features

* Initial version
