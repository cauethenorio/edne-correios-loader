# e-DNE Correios Loader

[![PyPI - Version](https://img.shields.io/pypi/v/edne-correios-loader.svg)](https://pypi.org/project/edne-correios-loader)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/edne-correios-loader.svg)](https://pypi.org/project/edne-correios-loader)
[![codecov](https://codecov.io/gh/cauethenorio/edne-correios-loader/graph/badge.svg?token=HP9C86U1LX)](https://codecov.io/gh/cauethenorio/edne-correios-loader)

Carregue todos os CEPs do Brasil no seu banco de dados com um único comando.

O e-DNE (Diretório Nacional de Endereços) dos Correios contém mais de 1,5 milhão de CEPs e está disponível gratuitamente.

Esta ferramenta baixa automaticamente a versão mais recente, processa os arquivos e carrega em qualquer banco de dados (PostgreSQL, MySQL, SQLite, etc.), criando uma tabela unificada pronta para consulta.

```shell
uvx edne-correios-loader load --database-url sqlite:///dne.db
```

---

### [English version 🇺🇸](README-en.md)


## Quick Start

Com [uv](https://docs.astral.sh/uv/) instalado, execute diretamente sem precisar instalar:

```shell
uvx edne-correios-loader load --database-url sqlite:///dne.db
```

Para PostgreSQL:

```shell
uvx --from 'edne-correios-loader[postgresql]' edne-correios-loader load \
  --database-url postgresql://user:pass@localhost:5432/mydb
```

Após a importação, consulte CEPs:

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


## O que faz

- Baixa automaticamente o e-DNE Básico do site dos Correios
- Processa os arquivos de texto e carrega em um banco de dados
- Cria uma tabela unificada para consulta de CEPs (não inclusa no DNE original)
- Suporta PostgreSQL, MySQL, SQLite e outros bancos via SQLAlchemy
- Permite personalizar os nomes das tabelas criadas
- Atualiza os dados sem interrupção do serviço (transação atômica)
- Atualizações quinzenais: basta rodar o comando novamente


## Instalação

Caso prefira instalar o pacote ao invés de usar `uvx`:

```shell
pip install edne-correios-loader
```

Também será necessário instalar o driver do banco de dados que será utilizado:

### PostgreSQL

```shell
pip install edne-correios-loader[postgresql]
```

Se não houver uma versão compilada do `psycopg2` para seu sistema operacional e versão do python,
outra opção é instalar o driver `pg8000`, escrito totalmente em Python.

### MySQL

```shell
pip install edne-correios-loader[mysql]
```

### SQLite

O Python já disponibiliza a biblioteca `sqlite3`, não é necessária nenhuma instrução adicional.

### Outros

Qualquer banco de dados suportado pelo [SQLAlchemy](https://docs.sqlalchemy.org/en/20/dialects/index.html) pode ser utilizado, como Microsoft SQL Server e Oracle.


## Utilização

### Linha de comando

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

#### Opções

- __`--dne-source`__ **(opcional)**

  Origem do e-DNE a ser importado. Pode ser:
    - Uma URL apontando para um arquivo ZIP com o e-DNE
    - O caminho local para um arquivo ZIP com o e-DNE
    - O caminho local para um diretório contendo os arquivos do e-DNE

  Se essa opção não for informada, o último e-DNE Básico disponível no site dos
  Correios será baixado automaticamente e utilizado como fonte.


- __`--database-url`__ **(obrigatório)**

  URL do banco de dados onde os dados do e-DNE serão importados. A URL deve seguir o
  padrão `dialect+driver://username:password@host:port/database`, onde:
    - `dialect` é o nome do banco de dados, como `postgresql`, `mysql`, `sqlite`, etc.
    - `driver` é o nome do driver do banco de dados, como `psycopg2`, `mysqlclient`,
      `pg8000`, etc. Se não especificado, o driver mais popular é utilizado automaticamente.
    - `username` é o nome de usuário do banco de dados
    - `password` é a senha do usuário do banco de dados
    - `host` é o endereço do servidor do banco de dados
    - `port` é a porta do servidor do banco de dados
    - `database` é o nome do banco de dados

  Mais informações sobre o formato da URL podem ser encontradas na documentação do
    [SQLAlchemy](https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls)


- __`--tables`__ **(opcional)**

  Define quais tabelas serão mantidas no banco de dados após a importação. Pode ser:
    - `unified-cep-only`: Mantém apenas a tabela unificada de CEPs
    - `cep-tables`: Mantém apenas as tabelas com CEPs, separadas por tipo
    - `all`: Mantém todas as tabelas do DNE

  Quando não especificado, a opção `unified-cep-only` é utilizada por padrão, mantendo
  apenas a tabela unificada de CEPs.


- __`--table-name`__ **(opcional)**

  Permite personalizar o nome de uma tabela no banco de dados. Pode ser utilizado múltiplas
  vezes para renomear várias tabelas. O formato é `original=custom`, onde `original` é o
  nome padrão da tabela e `custom` é o nome desejado.

  Exemplo: `--table-name cep_unificado=correios_cep`

  Útil para integrar com projetos que seguem convenções de nomeação das tabelas.


- __`--verbose`__ **(opcional)**

  Habilita o modo verboso, que exibe informações de DEBUG úteis para resolver problemas
  na execução do comando

#### Exemplos de uso

Importa o e-DNE Básico direto do site dos Correios para um banco de dados SQLite local:
```shell
edne-correios-loader load --database-url sqlite:///dne.db
```

O mesmo para PostgreSQL:
```shell
edne-correios-loader load --database-url postgresql://user:pass@localhost:5432/mydb
```

Renomeando a tabela unificada:
```shell
edne-correios-loader load \
  --database-url sqlite:///dne.db \
  --table-name cep_unificado=correios_cep
```

#### Consulta de CEPs

Após a importação, é possível checar se os dados foram importados corretamente consultando
CEPs na tabela unificada através do comando `edne-correios-loader query-cep`.

Se a tabela unificada foi renomeada durante a importação, use a opção `--cep-table-name`:
```shell
edne-correios-loader query-cep --database-url sqlite:///dne.db --cep-table-name correios_cep 01001000
```


### API Python

O `edne-correios-loader` também pode ser utilizado como uma biblioteca Python, através
do módulo `edne_correios_loader`. Exemplo:

```python
from edne_correios_loader import DneLoader, TableSetEnum

DneLoader(
  # URL de conexão com o banco de dados (obrigatório)
  'postgresql://user:pass@localhost:5432/mydb',
  # Caminho ou URL para o arquivo ZIP ou diretório com os arquivos do e-DNE (opcional)
  # Quando omitido, o e-DNE será baixado automaticamente do site dos Correios
  dne_source="/path/to/dne.zip",
  # Personaliza os nomes das tabelas no banco de dados (opcional)
  # Aceita um dict ou um callable que transforma os nomes
  table_names={"cep_unificado": "correios_cep"},
).load(
  # Quais tabelas manter no banco de dados após a importação (opcional)
  # quando omitido apenas a tabela unificada é mantida
  # Outras opções são TableSetEnum.CEP_TABLES e TableSetEnum.ALL
  table_set=TableSetEnum.CEP_TABLES
)
```

O parâmetro `table_names` também aceita um callable para transformar todos os nomes:
```python
DneLoader(
  'sqlite:///dne.db',
  table_names=lambda name: f"dne_{name}",  # dne_cep_unificado, dne_log_localidade, etc.
).load()
```

Após a importação, os CEPs podem ser consultados na tabela unificada através da classe `CepQuerier`:
```python
from edne_correios_loader import CepQuerier

# Se a tabela foi renomeada, informe o nome personalizado
cep_querier = CepQuerier(
  'postgresql://user:pass@localhost:5432/mydb',
  cep_table_name='correios_cep',  # opcional, padrão: 'cep_unificado'
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

## Atualização dos CEPs

Quinzenalmente os Correios atualizam o e-DNE com novos CEPs. Para atualizar sua base de dados,
basta executar novamente o comando `load`. O e-DNE mais recente será baixado
automaticamente do site dos Correios.

Todo o processo é executado em uma transação, portanto, outros clientes conectados no banco
continuarão tendo acesso aos dados antigos enquanto a atualização é executada.
Se algo der errado durante a atualização, a transação será desfeita e os dados antigos serão mantidos.

## Testes

Para executar os testes, é necessário a instalação do [Docker](https://www.docker.com/) e do
[uv](https://docs.astral.sh/uv/). Após a instalação:
1. Clone o projeto:
  ```shell
  git clone https://github.com/cauethenorio/edne-correios-loader
  ```
2. Rode os containers Docker com MySQL e PostgreSQL:
  ```shell
  cd edne-correios-loader/tests
  docker compose up -d
  ```
3. Execute os testes usando o `uv`:
  ```shell
  uv run pytest tests
  ```

## ClickHouse

Também é possível carregar o e-DNE diretamente no ClickHouse com o comando `sync-clickhouse`.

### Instalação

Para usar o suporte a ClickHouse, instale o extra correspondente:

```shell
pip install edne-correios-loader[clickhouse]
```

### Linha de comando

Execução com configurações padrão (`localhost:9000`, banco `default`):

```shell
edne-correios-loader sync-clickhouse
```

Com servidor remoto e credenciais:

```shell
edne-correios-loader sync-clickhouse \
  -ch clickhouse.example.com \
  -cp 9000 \
  -cdb dne \
  -cu admin \
  -cpw senha123
```

Com arquivo e-DNE específico:

```shell
edne-correios-loader sync-clickhouse \
  -s ./dne_2026.zip \
  --tables unified-cep-only
```

#### Opções principais

- __`-s, --dne-source`__ caminho/URL com arquivo ou diretório do e-DNE
- __`-ch, --clickhouse-host`__ host do servidor ClickHouse (padrão: `localhost`)
- __`-cp, --clickhouse-port`__ porta do servidor ClickHouse (padrão: `9000`)
- __`-cdb, --clickhouse-database`__ banco de dados (padrão: `default`)
- __`-cu, --clickhouse-user`__ usuário (padrão: `default`)
- __`-cpw, --clickhouse-password`__ senha (padrão: vazio)
- __`--tables`__ tabelas a manter após importação (`unified-cep-only`, `cep-tables`, `all`)
- __`--table-name`__ renomeia tabelas (`--table-name original=custom`)
- __`--verbose`__ habilita logs detalhados


## Licença

Esse projeto é distribuído sob os termos da licença [MIT](https://spdx.org/licenses/MIT.html).
