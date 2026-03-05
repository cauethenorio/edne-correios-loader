# e-DNE Correios Loader

[![PyPI - Version](https://img.shields.io/pypi/v/edne-correios-loader.svg)](https://pypi.org/project/edne-correios-loader)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/edne-correios-loader.svg)](https://pypi.org/project/edne-correios-loader)
[![codecov](https://codecov.io/gh/cauethenorio/edne-correios-loader/graph/badge.svg?token=HP9C86U1LX)](https://codecov.io/gh/cauethenorio/edne-correios-loader)

Load all Brazilian postal codes (CEPs) into your database with a single command.

The e-DNE (National Address Directory) from Correios (Brazilian postal service) contains over 1.5 million postal codes and is freely available. This tool automatically downloads the latest version, processes the files and loads them into any database (PostgreSQL, MySQL, SQLite, etc.), creating a unified table ready for querying.

```shell
uvx edne-correios-loader load --database-url sqlite:///dne.db
```

---

### [Versão em português 🇧🇷](README.md)


## Quick Start

With [uv](https://docs.astral.sh/uv/) installed, run directly without installing:

```shell
uvx edne-correios-loader load --database-url sqlite:///dne.db
```

For PostgreSQL:

```shell
uvx --from 'edne-correios-loader[postgresql]' edne-correios-loader load \
  --database-url postgresql://user:pass@localhost:5432/mydb
```

After the import, query CEPs:

```shell
$ edne-correios-loader query-cep --database-url sqlite:///dne.db 01001000
{
  "cep": "01001000",
  "logradouro": "Praça da Sé",
  "complemento": null,
  "bairro": "Sé",
  "municipio": "São Paulo",
  "municipio_cod_ibge": 3550308,
  "uf": "SP",
  "nome": null
}
```


## What it does

- Automatically downloads the e-DNE Básico from the Correios website
- Processes the text files and loads them into a database
- Creates a unified table for querying postal codes (not included in the original DNE)
- Supports PostgreSQL, MySQL, SQLite and other databases via SQLAlchemy
- Allows customizing the names of created tables
- Updates data without service interruption (atomic transaction)
- Biweekly updates: just run the command again


## Installation

If you prefer to install the package instead of using `uvx`:

```shell
pip install edne-correios-loader
```

You will also need to install the database driver that will be used:

### PostgreSQL

```shell
pip install edne-correios-loader[postgresql]
```

If there is no pre-compiled version of `psycopg2` for your operating system and Python version,
another option is to install the `pg8000` driver, which is written entirely in Python.

### MySQL

```shell
pip install edne-correios-loader[mysql]
```

### SQLite

Python already provides the `sqlite3` library, so no additional instructions are needed.

### Others

Any database supported by [SQLAlchemy](https://docs.sqlalchemy.org/en/20/dialects/index.html) can be used, such as Microsoft SQL Server and Oracle.


## Usage

### Command Line

```shell
$ edne-correios-loader load --help

Usage: edne-correios-loader load [OPTIONS]

  Load DNE data into a database.

Options:
  -s, --dne-source <path/zip-file/url>
                                  Path or URL with the DNE file/dir to be
                                  imported
  -db, --database-url <url>       Database URL where the DNE data will be
                                  imported to  [required]
  --tables [unified-cep-only|cep-tables|all]
                                  Which tables to keep in the database after
                                  the import
  --table-name <original=custom>  Rename a table: --table-name original=custom
  -v, --verbose                   Enables verbose mode.
  -h, --help                      Show this message and exit.
```

#### Options

- __`--dne-source`__ **(optional)**

  Source of the e-DNE to be imported. It can be:
    - A URL to a ZIP file with the e-DNE
    - The local path to a ZIP file with the e-DNE
    - The local path to a directory containing the e-DNE files

  If this option is not provided, the latest e-DNE Basic will be automatically
  downloaded from the Correios website and used as the source.


- __`--database-url`__ **(required)**

  Database URL where the e-DNE data will be imported. The URL should follow the format
  `dialect+driver://username:password@host:port/database`, where:
    - `dialect` is the name of the database, such as `postgresql`, `mysql`, `sqlite`, etc.
    - `driver` is the name of the database driver, such as `psycopg2`, `mysqlclient`,
      `pg8000`, etc. If not specified, the most popular driver is automatically used.
    - `username` is the database user's name
    - `password` is the database user's password
    - `host` is the database server's address
    - `port` is the database server's port
    - `database` is the name of the database

  More information about the URL format can be found in the
    [SQLAlchemy documentation](https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls)


- __`--tables`__ **(optional)**

  Defines which tables will be kept in the database after the import. It can be:
    - `unified-cep-only`: Keeps only the unified CEP table
    - `cep-tables`: Keeps only the tables with CEPs, separated by type
    - `all`: Keeps all DNE tables

  When not specified, the `unified-cep-only` option is used by default, keeping
  only the unified CEP table.


- __`--table-name`__ **(optional)**

  Allows customizing a table name in the database. Can be used multiple times
  to rename several tables. The format is `original=custom`, where `original` is the
  default table name and `custom` is the desired name.

  Example: `--table-name cep_unificado=correios_cep`

  Useful for integrating with projects that follow table naming conventions.


- __`--verbose`__ **(optional)**

  Enables verbose mode, which displays DEBUG information useful for troubleshooting
  during command execution.

#### Usage Examples

Imports the e-DNE Basic directly from the Correios website to a local SQLite database:
```shell
edne-correios-loader load --database-url sqlite:///dne.db
```

Same for PostgreSQL:
```shell
edne-correios-loader load --database-url postgresql://user:pass@localhost:5432/mydb
```

Renaming the unified table:
```shell
edne-correios-loader load \
  --database-url sqlite:///dne.db \
  --table-name cep_unificado=correios_cep
```

#### CEP Query

After the import, it's possible to check if the data was imported correctly by querying
CEPs in the unified table using the command `edne-correios-loader query-cep`.

If the unified table was renamed during import, use the `--cep-table-name` option:
```shell
edne-correios-loader query-cep --database-url sqlite:///dne.db --cep-table-name correios_cep 01001000
```


### Python API

The `edne-correios-loader` can also be used as a Python library, through
the `edne_correios_loader` module. Example:

```python
from edne_correios_loader import DneLoader, TableSetEnum

DneLoader(
  # Database connection URL (required)
  'postgresql://user:pass@localhost:5432/mydb',
  # Path or URL to the ZIP file or directory with e-DNE files (optional)
  # When omitted, the e-DNE will be automatically downloaded from the Correios website
  dne_source="/path/to/dne.zip",
  # Customize table names in the database (optional)
  # Accepts a dict or a callable that transforms the names
  table_names={"cep_unificado": "correios_cep"},
).load(
  # define the tables to keep in the database after the import (optional)
  # When omitted, only the unified table is kept
  # Other options are TableSetEnum.CEP_TABLES and TableSetEnum.ALL
  table_set=TableSetEnum.CEP_TABLES
)
```

The `table_names` parameter also accepts a callable to transform all names:
```python
DneLoader(
  'sqlite:///dne.db',
  table_names=lambda name: f"dne_{name}",  # dne_cep_unificado, dne_log_localidade, etc.
).load()
```

After the import, CEPs can be queried in the unified table using the `CepQuerier` class:
```python
from edne_correios_loader import CepQuerier

# If the table was renamed, provide the custom name
cep_querier = CepQuerier(
  'postgresql://user:pass@localhost:5432/mydb',
  cep_table_name='correios_cep',  # optional, default: 'cep_unificado'
)
cep = cep_querier.query('01319010')

assert cep == {
  'cep': '79290000',
  'logradouro': None,
  'complemento': None,
  'bairro': None,
  'municipio': 'Bonito',
  'municipio_cod_ibge': 5002209,
  'uf': 'MS',
  'nome': None
}
```

## Updating CEPs data

Every two weeks, Correios updates the e-DNE with new postal codes. To update your database,
simply run the `load` command again. The latest e-DNE will be automatically downloaded from
the Correios website.

The whole process is executed inside a transaction, so other clients connected to the database
will continue to have access to the old data while the update is being executed.
If something goes wrong during the update, the transaction will be rolled back and the old data will be preserved.


## Tests

To run the tests, you need to have [Docker](https://www.docker.com/) and
[uv](https://docs.astral.sh/uv/) installed. After installation:
1. Clone the project:
  ```shell
  git clone https://github.com/cauethenorio/edne-correios-loader
  ```
2. Run the Docker containers with MySQL and PostgreSQL:
  ```shell
  cd edne-correios-loader/tests
  docker compose up -d
  ```
3. Execute the tests using `uv`:
  ```shell
  uv run pytest tests
  ```

## License

This project is distributed under the terms of the [MIT license](https://spdx.org/licenses/MIT.html).
