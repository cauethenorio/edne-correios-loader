# e-DNE Correios Loader

[![PyPI - Version](https://img.shields.io/pypi/v/edne-correios-loader.svg)](https://pypi.org/project/edne-correios-loader)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/edne-correios-loader.svg)](https://pypi.org/project/edne-correios-loader
[![codecov](https://codecov.io/gh/cauethenorio/edne-correios-loader/graph/badge.svg?token=HP9C86U1LX)](https://codecov.io/gh/cauethenorio/edne-correios-loader)

CLI to load e-DNE Basico files from Correios (Brazilian postal service) into a database
(PostgreSQL, MySQL, SQLite, and others) and create a single table for querying postal codes (CEPs).

---

### [Versão em português 🇧🇷](README.md)

## Features

- Import Correios' e-DNE Basico files into a database
- Creates a unified table for querying postal codes (CEPs)
- Supports databases like PostgreSQL, MySQL, SQLite, and others
- Allows for data updates without service interruption
 

## Purpose

The DNE (National Address Directory) is an official and exclusive database of Correios
(Brazilian postal service), containing over 900 thousand postal codes from all over Brazil.
It consists of addressing elements (description of streets, neighborhoods, municipalities,
villages, hamlets) and Postal Address Codes - CEP.

This database is available in two versions, the __e-DNE Basic__ and the __e-DNE Master__.
Both contain all the postal codes in Brazil, with addressing elements down to the street section level,
but they differ in format. The e-DNE Basic is composed of several text files (`.txt`) that need
to be processed and transferred to a database in order to be queried. On the other hand, the
e-DNE Master is a database in MS-Access format (`.mdb`) ready for use.

The DNE is owned by Correios and can be purchased through their e-commerce platform. Currently,
(October 2023), the Master version costs R$ 3,187.65 and the Basic version costs R$ 1,402.5.
Both versions guarantee one year of updates after the purchase date.

[__For clients with a contract with Correios, the e-DNE Basic can be acquired for free.__](https://www.correios.com.br/enviar/marketing-direto/saiba-mais-nacional)

This project facilitates the use of the e-DNE Basic, which is cheaper and easier to acquire,
by processing the text files and transferring them to a database. It also creates a
single table for querying postal codes (not included in the DNE, where different types of
postal codes are stored in different tables) and allows your database to be updated with
new versions of the e-DNE, released biweekly by Correios.


## Installation

The `edne-correios-loader` can be installed via `pip`:

```shell
pip install edne-correios-loader
```

You will also need to install the database driver that will be used. Here are some
instructions on how to install drivers for the most common databases:

### PostgreSQL

For PostgreSQL, the `psycopg2-binary` driver can be installed using an
[extra](https://peps.python.org/pep-0508/#extras):
```shell
pip install edne-correios-loader[postgresql]
```

If there are no pre-compiled version of `psycopg2` for your operating system and Python version,
you may need to install some libraries to be able to compile the driver. Another option is to install the
`pg8000` driver for PostgreSQL, which is written entirely in Python and does not need to be compiled.

### MySQL

For MySQL, the `mysqlclient` driver can be installed using an
[extra](https://peps.python.org/pep-0508/#extras):
```shell
pip install edne-correios-loader[mysql]
```

### SQLite

Python already provides the `sqlite3` library for communication with SQLite, so no
additional instructions are needed.

### Others

The `sqlalchemy` library is used for communication with the database, so any database
supported by it can be used, such as Microsoft SQL Server and Oracle. To install
the driver for a database not listed here, refer to the SQLAlchemy documentation:
https://docs.sqlalchemy.org/en/20/dialects/index.html



## Usage

### Command Line

The data import can be executed via the command line using the `edne-correios-loader load` command.

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
  -v, --verbose                   Enables verbose mode.
  -h, --help                      Show this message and exit.
```

#### Options

The following options are available:
- __`--dne-source`__ **(optional)**

  Source of the e-DNE to be imported. It can be:
    - A URL to a ZIP file with the e-DNE
    - The local path to a ZIP file with the e-DNE
    - The local path to a directory containing the e-DNE files
    
  If this option is not provided, the latest available e-DNE Basic on the Correios website
  will be downloaded and used as the source. **Use this option only if you have a contract
  with Correios**.
 

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


- __`--verbose`__ **(optional)**

  Enables verbose mode, which displays DEBUG information useful for troubleshooting
  during command execution.

#### Usage Examples

Imports the e-DNE Basic directly from the Correios website to a local SQLite database,
keeping only the unified table:
```shell
edne-correios-loader load --database-url sqlite:///dne.db
```

Imports the e-DNE Basic from a ZIP file to a local PostgreSQL database, keeping all
tables with CEPs:
```shell
edne-correios-loader load \
  --dne-source /path/to/dne.zip \
  --database-url postgresql://user:pass@localhost:5432/mydb \
  --tables cep-tables
```

Imports the e-DNE Basic from a directory to a local MySQL database, keeping all tables:
```shell
edne-correios-loader load \
  --dne-source /path/to/dne/dir \
  --database-url mysql+mysqlclient://user:pass@localhost:3306/mydb \
  --tables all
```

The command output may vary depending on the options used, but it should be
similar to the following:
```
Starting DNE Correios Loader v0.1.1

Connecting to database...

Resolving DNE source...

No DNE source provided, the latest DNE will be downloaded from Correios website
Downloading DNE file  [####################################]  100%

Creating tables:
- cep_unificado
- log_localidade
- log_bairro
- log_cpc
- log_logradouro
- log_grande_usuario
- log_unid_oper

Cleaning tables

Populating table log_localidade
  Reading LOG_LOCALIDADE.TXT
  Inserted 11219 rows into table "log_localidade"

Populating table log_bairro
  Reading LOG_BAIRRO.TXT
  Inserted 64456 rows into table "log_bairro"

Populating table log_cpc
  Reading LOG_CPC.TXT
  Inserted 2133 rows into table "log_cpc"

Populating table log_logradouro
  Reading LOG_LOGRADOURO_RS.TXT
  Reading LOG_LOGRADOURO_RR.TXT
  Reading LOG_LOGRADOURO_SC.TXT
  Reading LOG_LOGRADOURO_SP.TXT
  Reading LOG_LOGRADOURO_SE.TXT
  Reading LOG_LOGRADOURO_PI.TXT
  Reading LOG_LOGRADOURO_MS.TXT
  Reading LOG_LOGRADOURO_AP.TXT
  Reading LOG_LOGRADOURO_MG.TXT
  Reading LOG_LOGRADOURO_MT.TXT
  Reading LOG_LOGRADOURO_AC.TXT
  Reading LOG_LOGRADOURO_MA.TXT
  Reading LOG_LOGRADOURO_TO.TXT
  Reading LOG_LOGRADOURO_AL.TXT
  Reading LOG_LOGRADOURO_CE.TXT
  Reading LOG_LOGRADOURO_BA.TXT
  Reading LOG_LOGRADOURO_AM.TXT
  Reading LOG_LOGRADOURO_ES.TXT
  Reading LOG_LOGRADOURO_PR.TXT
  Reading LOG_LOGRADOURO_PE.TXT
  Reading LOG_LOGRADOURO_GO.TXT
  Reading LOG_LOGRADOURO_RN.TXT
  Reading LOG_LOGRADOURO_RO.TXT
  Reading LOG_LOGRADOURO_DF.TXT
  Reading LOG_LOGRADOURO_RJ.TXT
  Reading LOG_LOGRADOURO_PB.TXT
  Reading LOG_LOGRADOURO_PA.TXT
  Inserted 1236944 rows into table "log_logradouro"

Populating table log_grande_usuario
  Reading LOG_GRANDE_USUARIO.TXT
  Inserted 18967 rows into table "log_grande_usuario"

Populating table log_unid_oper
  Reading LOG_UNID_OPER.TXT
  Inserted 12534 rows into table "log_unid_oper"

Populating unified CEP table
  Populating unified CEP table with logradouros data
    Inserted 1236944 CEPs from logradouros into table cep_unificado
  Populating unified CEP table with localidades data
    Inserted 4974 CEPs from localidades into table cep_unificado
  Populating unified CEP table with localidades subordinadas data
    Inserted 5311 CEPs from localidades subordinadas into table cep_unificado
  Populating unified CEP table with normalized CPC data
    Inserted 2133 CEPs from CPC into table cep_unificado
  Populating unified CEP table with normalized grandes usuários data
    Inserted 18967 CEPs from grandes usuários into table cep_unificado
  Populating unified CEP table with normalized unidades operacionais data
    Inserted 12534 CEPs from unidades operacionais into table cep_unificado
  Inserted 1280863 rows into table "cep_unificado"

Dropping tables
  Dropping table log_faixa_uop
  Dropping table log_var_log
  Dropping table log_unid_oper
  Dropping table log_num_sec
  Dropping table log_grande_usuario
  Dropping table log_var_bai
  Dropping table log_logradouro
  Dropping table log_faixa_cpc
  Dropping table log_faixa_bairro
  Dropping table log_var_loc
  Dropping table log_faixa_localidade
  Dropping table log_cpc
  Dropping table log_bairro
  Dropping table log_localidade
  Dropping table log_faixa_uf
  Dropping table ect_pais
```

#### CEP Query

After the import, it's possible to check if the data was imported correctly by querying
CEPs in the unified table using the command `edne-correios-loader query-cep`. Example:

```shell
$ edne-correios-loader query-cep --database-url mysql+mysqlclient://user:pass@localhost:3306/mydb 01001000
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


### Python API

The `edne-correios-loader` can also be used as a Python library, through
the `edne_correios_loader` module. Example:

```python
from edne_correios_loader import DneLoader, TableSetEnum

DneLoader(
  # Database connection URL (required)
  'postgresql://user:pass@localhost:5432/mydb',
  # Path or URL to the ZIP file or directory with e-DNE files (optional) 
  dne_source="/path/to/dne.zip",
).load(
  # define the tables to keep in the database after the import (optional)
  # When omitted, only the unified table is kept
  # Other options are TableSetEnum.CEP_TABLES and TableSetEnum.ALL
  table_set=TableSetEnum.CEP_TABLES
)
```

After the import, CEPs can be queried in the unified table using the `CepQuerier` class:
```python
from edne_correios_loader import CepQuerier

cep_querier = CepQuerier('postgresql://user:pass@localhost:5432/mydb')
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

Bi-weekly, Correios update the e-DNE with new postal codes. To update your database,
run the `loader` command using the updated e-DNE file as the source.

The command will delete the data from all e-DNE tables and import the data from the new e-DNE.
After the import, the unified table is repopulated with the new data.

The whole process is executed inside a transaction, so other clients connected to the database
will continue to have access to the old data while the update is being executed.

If something goes wrong during the update, the transaction will be rolled back and the old data will be preserved.


## Tests

To run the tests, you need to have [Docker](https://www.docker.com/) and
[Python project manager Hatch](https://github.com/pypa/hatch) installed. After installation:
1. Clone the project:
  ```shell
  git clone https://github.com/cauethenorio/edne-correios-loader
  ```` 
2. Run the Docker containers with MySQL and PostgreSQL:
  ```shell
  cd edne-correios-loader/tests
  docker compose up -d
  ```
3. Execute the tests using `hatch`:
  ```shell
  hatch run test
  ``` 

## License

This project is distributed under the terms of the [MIT license](https://spdx.org/licenses/MIT.html).