### (unreleased)
    * Attempt to fix temporary file handling on Windows (WinError 32) (fixes #4)
    * Fix vulnerability: Bumped cryptography from 46.0.4 to 46.0.5

### v1.0.0 (2026-02-10)
    * Dropped Python 3.8 and 3.9 support, which reached EOL
    * Added Python 3.14 support
    * Migrated tooling from hatch to uv
    * Fixed compatibility with Click 8.2+
    * Added instructions on how to use it with uvx

### v0.2.0 (2025-02-23)
    * Added compatibility with python 3.13
    * Updated db writer to skip CEPs without municipality IBGE code when populating cep_unificado

### v0.1.3 (2024-06-03)
    * Fixed incompatibility with MS SQL Server (fixes #3)
    * Replaced Black with Ruff for code formatting

### v0.1.2 (2023-10-11)
    * Added compatibility with python 3.8

### v0.1.1 (2023-10-06)
    * Improved README and added english version
    * Added extras for MySQL and PostgreSQL driver installation 

### v0.1.0 (2023-10-06)
    * Initial version