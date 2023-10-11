# e-DNE Correios Loader

[![PyPI - Version](https://img.shields.io/pypi/v/edne-correios-loader.svg)](https://pypi.org/project/edne-correios-loader)
[![PyPI - Python Version](https://img.shields.io/pypi/pyversions/edne-correios-loader.svg)](https://pypi.org/project/edne-correios-loader)
[![codecov](https://codecov.io/gh/cauethenorio/edne-correios-loader/graph/badge.svg?token=HP9C86U1LX)](https://codecov.io/gh/cauethenorio/edne-correios-loader)

Programa de linha de comando para carregar arquivos do e-DNE Basico dos Correios para um banco de
dados (PostgreSQL, MySQL, SQLite e outros) e criar uma tabela única para consulta de CEPs.

---

### [English version 🇺🇸](README-en.md)

## Funcionalidades

- Carrega arquivos do DNE Básico dos Correios para um banco de dados
- Cria uma tabela unificada para consulta de CEPs
- Suporta os bancos de dados PostgreSQL, MySQL, SQLite entre outros
- Permite atualização dos dados sem interrupção do serviço
 

## Propósito

O DNE (Diretório Nacional de Endereços) é um banco de dados oficial e exclusivo dos Correios,
que contém mais de 900 mil CEP de todo o Brasil, constituído de elementos de endereçamento
(descrição de logradouros, bairros, municípios, vilas, povoados) e Códigos de Endereçamento
Postal - CEP.

Esse banco de dados é disponibilizado em duas versões, o __e-DNE Básico__ e o __e-DNE Máster__.
Ambas contêm todos os CEPs do Brasil, com elementos de endereçamento até nível de seção
de logradouro, porém diferem no formato. O e-DNE Básico é composto por vários arquivos de texto
(`.txt`) que precisam ser processados e transferidos para um banco de dados para poderem ser
consultados. Já o e-DNE Máster é um banco de dados no formato MS-Access (`.mdb`) pronto para uso.

O DNE é de propriedade dos Correios e pode ser adquirido através de seu e-commerce. Atualmente
(Outubro de 2023) a versão Máster custa R$ 3.187,65 e a versão Básica custa R$ 1.402,5.
Ambas as versões garantem um ano de atualizações após a data da compra.

[__Para clientes com contrato com os Correios, o e-DNE Básico pode ser adquirido gratuitamente.__](https://www.correios.com.br/enviar/marketing-direto/saiba-mais-nacional)

Esse projeto facilita o uso do e-DNE Básico, que é mais barato e mais fácil de ser adquirido,
processando os arquivos de texto e transferindo-os para um banco de dados, ele também cria uma
tabela única para consulta de CEPs (não inclusa no DNE, onde CEPs de diferentes tipos ficam em
tabelas diferentes) e permite que sua base seja atualizada com novas versões do e-DNE, lançadas
quinzenalmente pelos Correios.


## Instalação

O `edne-correios-loader` pode ser instalado através do `pip`:

```shell
pip install edne-correios-loader
```

Também será necessário instalar o driver do banco de dados que será utilizado. Aqui estão algumas
instruções de como instalar os drivers para os bancos de dados mais comuns:

### PostgreSQL

Para o PostgreSQL, o driver `psycopg2-binary` pode ser instalado utilizando um
[extra](https://peps.python.org/pep-0508/#extras):
```shell
pip install edne-correios-loader[postgresql]
```

Se não houver uma versão compilada do `psycopg2` para seu sistema operacional e versão do python,
você precisará instalar algumas bibliotecas para poder compilar o driver. Outra opção é instalar o
driver `pg8000` para o PostgreSQL, que é escrito totalmente em Python e não precisa ser compilado.

### MySQL

Para o MySQL, o driver `mysqlclient` pode ser instalado utilizando um
[extra](https://peps.python.org/pep-0508/#extras):
```shell
pip install edne-correios-loader[mysql]
```

### SQLite

O Python já disponibiliza a biblioteca `sqlite3` para comunicação com o SQLite, portanto não é
necessária nenhuma instrução adicional.

### Outros

A biblioteca `sqlalchemy` é utilizada para comunicação com o banco de dados, portanto qualquer banco
de dados suportado por ela pode ser utilizado, como o Microsoft SQL Server e Oracle. Para instalar
o driver de um banco de dados não listado aqui, consulte a documentação do SQLAlchemy:
https://docs.sqlalchemy.org/en/20/dialects/index.html


## Utilização

### Linha de comando

A importação dos dados pode ser executada através da linha de comando, com o
comando `edne-correios-loader load`.

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

#### Opções

As seguintes opções estão disponíveis:
- __`--dne-source`__ **(opcional)**

  Origem do e-DNE a ser importado. Pode ser:
    - Uma URL apontando para um arquivo ZIP com o e-DNE
    - O caminho local para um arquivo ZIP com o e-DNE
    - O caminho local para um diretório contendo os arquivos do e-DNE
    
  Se essa opcão não for informada, o último e-DNE Básico disponível no site dos
  Correios será baixado e usado como fonte. **Utilize essa opção apenas se você
  tiver um contrato com os Correios**.
 

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


- __`--verbose`__ **(opcional)**

  Habilita o modo verboso, que exibe informações de DEBUG úteis para resolver problemas
  na execução do comando

#### Exemplos de uso

Importa o e-DNE Básico direto do site dos correios para um banco de dados SQLite local,
mantendo apenas a tabela unificada:
```shell
edne-correios-loader load --database-url sqlite:///dne.db
```

Importa o e-DNE Básico de um arquivo ZIP para um banco de dados PostgreSQL local, mantendo
todas as tabelas com CEPs:
```shell
edne-correios-loader load \
  --dne-source /path/to/dne.zip \
  --database-url postgresql://user:pass@localhost:5432/mydb \
  --tables cep-tables
```

Importa o e-DNE Básico de um diretório para um banco de dados MySQL local, mantendo todas
as tabelas:
```shell
edne-correios-loader load \
  --dne-source /path/to/dne/dir \
  --database-url mysql+mysqlclient://user:pass@localhost:3306/mydb \
  --tables all
```

O output do comando deve variar conforme as opções utilizadas, mas deve ser
parecido com o seguinte:
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

#### Consulta de CEPs

Após a importação, é possível checar se os dados foram importados corretamente consultando
CEPs na tabela unificada através do comando `edne-correios-loader query-cep`. Exemplo:

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


### API Python

O `edne-correios-loader` também pode ser utilizado como uma biblioteca Python, através
do módulo `edne_correios_loader`. Exemplo:

```python
from edne_correios_loader import DneLoader, TableSetEnum

DneLoader(
  # URL de conexão com o banco de dados (obrigatório)
  'postgresql://user:pass@localhost:5432/mydb',
  # Caminho ou URL para o arquivo ZIP ou diretório com os arquivos do e-DNE (opcional) 
  dne_source="/path/to/dne.zip",
).load(
  # Quais tabelas manter no banco de dados após a importação (opcional)
  # quando omitido apenas a tabela unificada é mantida
  # Outras opções são TableSetEnum.CEP_TABLES e TableSetEnum.ALL
  table_set=TableSetEnum.CEP_TABLES
)
```

Após a importação, os CEPs podem ser consultados na tabela unificada através da classe `CepQuerier`:
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

## Atualização dos CEPs

Quinzenalmente os Correios atualizam o e-DNE com novos CEPs. Para atualizar sua base de dados,
execute o comando `loader` utilizando o e-DNE atualizado como fonte.

O comando irá apagar os dados de todas as tabelas do e-DNE e importar os dados do novo e-DNE.
Após a importação a tabela unificada é re-populada com os novos dados.

Todo o processo é executado em uma transação, portanto, outros clientes conectados no banco
continuarão tendo acesso aos dados antigos enquanto a atualização é executada.

Se algo der errado durante a atualização, a transação será desfeita e os dados antigos serão mantidos.


## Testes

Para executar os testes, é necessário a instalação do [Docker](https://www.docker.com/) e do
[gerenciador de projetos Python Hatch](https://github.com/pypa/hatch). Após a instalação:
1. Clone o projeto:
  ```shell
  git clone https://github.com/cauethenorio/edne-correios-loader
  ```` 
2. Rode os containers Docker com MySQL e PostgreSQL:
  ```shell
  cd edne-correios-loader/tests
  docker compose up -d
  ```
3. Execute os testes usando o `hatch`:
  ```shell
  hatch run all:test
  ``` 

## Licença

Esse projeto é distribuído sob os termos da licença [MIT](https://spdx.org/licenses/MIT.html).
