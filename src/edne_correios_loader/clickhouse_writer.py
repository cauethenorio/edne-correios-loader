import logging
from collections.abc import Iterable
from urllib.parse import urlparse

from clickhouse_driver import Client

from .tables import metadata as default_metadata

logger = logging.getLogger(__name__)


class ClickHouseWriter:
    """
    Escreve dados do e-DNE em um banco de dados ClickHouse.
    
    Mantém a mesma interface do DneDatabaseWriter para
    consistência com o padrão do sistema.
    """

    client: object
    insert_buffer_size = 1000
    default_engine = "ReplacingMergeTree()"

    def __init__(
        self,
        host: str = "localhost",
        port: int = 9000,
        database: str = "default",
        user: str = "default",
        password: str = "",
        metadata: object = None,
    ):
        """
        Inicializa o escritor ClickHouse.
        
        Args:
            host: Hostname ou IP do servidor ClickHouse
            port: Porta do servidor ClickHouse
            database: Nome do banco de dados
            user: Usuário de autenticação
            password: Senha de autenticação
            metadata: Metadados SQLAlchemy (mantém compatibilidade com padrão)
        """
        self.host = host
        self.port = port
        self.database = database
        self.user = user
        self.password = password
        self.metadata = metadata or default_metadata
        self.client = None
        self.interface = "native"
        self.secure = False

        self.host, self.port = self._resolve_host_port(host, port)
        self.interface = self._detect_interface(self.port)
        self.secure = self.port == 8443

    def __enter__(self):
        logger.info("Conectando ao ClickHouse...", extra={"indentation": 0})
        if self.interface == "native":
            self.client = Client(
                self.host,
                port=self.port,
                database=self.database,
                user=self.user,
                password=self.password,
            )
        else:
            try:
                import clickhouse_connect
            except ImportError as exc:
                msg = (
                    "Para conectar em portas HTTP (ex: 8123), instale a dependência "
                    "'clickhouse-connect'."
                )
                raise RuntimeError(msg) from exc

            self.client = clickhouse_connect.get_client(
                host=self.host,
                port=self.port,
                username=self.user,
                password=self.password,
                database=self.database,
                interface="https" if self.secure else "http",
            )

        logger.info(
            "Conexão ClickHouse via protocolo %s em %s:%s",
            self.interface,
            self.host,
            self.port,
            extra={"indentation": 1},
        )
        # Testa a conexão
        self._execute("SELECT 1")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            if self.interface == "native":
                self.client.disconnect()
            else:
                self.client.close()
        
        if exc_val:
            logger.error(
                "Erro durante operações no ClickHouse",
                extra={"indentation": 0},
            )

    def create_tables(self, tables: list[str]):
        """
        Cria tabelas no ClickHouse.
        
        Args:
            tables: Lista de nomes de tabelas a criar
        """
        tables_names = "\n".join([f"- {t}" for t in tables])
        logger.info("Criando tabelas:\n%s", tables_names, extra={"indentation": 0})

        for table_name in tables:
            if table_name not in self.metadata.tables:
                logger.warning(
                    "Tabela %s não encontrada na definição de metadados",
                    table_name,
                    extra={"indentation": 1},
                )
                continue

            table = self.metadata.tables[table_name]
            create_sql = self._build_create_table_sql(table_name, table)
            
            try:
                self._execute(create_sql)
                logger.info(
                    "Tabela %s criada com sucesso",
                    table_name,
                    extra={"indentation": 1},
                )
            except Exception as e:
                logger.error(
                    "Erro ao criar tabela %s: %s",
                    table_name,
                    str(e),
                    extra={"indentation": 1},
                )

    def clean_tables(self, tables: list[str]):
        """
        Limpa o conteúdo das tabelas.
        
        Args:
            tables: Lista de nomes de tabelas a limpar
        """
        logger.info("Limpando tabelas", extra={"indentation": 0})

        for table_name in reversed(tables):
            try:
                self._execute(f"TRUNCATE TABLE {table_name}")
                logger.info(
                    "Tabela %s limpa",
                    table_name,
                    extra={"indentation": 1},
                )
            except Exception as e:
                logger.error(
                    "Erro ao limpar tabela %s: %s",
                    table_name,
                    str(e),
                    extra={"indentation": 1},
                )

    def drop_tables(self, tables: list[str]):
        """
        Remove tabelas do ClickHouse.
        
        Args:
            tables: Lista de nomes de tabelas a remover
        """
        if not tables:
            return

        logger.info("Removendo tabelas", extra={"indentation": 0})

        for table_name in reversed(tables):
            try:
                self._execute(f"DROP TABLE IF EXISTS {table_name}")
                logger.info(
                    "Tabela %s removida",
                    table_name,
                    extra={"indentation": 1},
                )
            except Exception as e:
                logger.error(
                    "Erro ao remover tabela %s: %s",
                    table_name,
                    str(e),
                    extra={"indentation": 1},
                )

    def populate_table(self, table_name: str, lines: Iterable[list[str]]):
        """
        Popula uma tabela com dados do e-DNE.
        
        Args:
            table_name: Nome da tabela a preencher
            lines: Iterável de linhas com dados (lista de strings)
        """
        logger.info("Preenchendo tabela %s", table_name, extra={"indentation": 0})
        
        if table_name not in self.metadata.tables:
            logger.error(
                "Tabela %s não encontrada na definição de metadados",
                table_name,
                extra={"indentation": 1},
            )
            return

        table = self.metadata.tables[table_name]
        columns = [c.name for c in table.columns]
        
        buffer = []
        count = 0

        for count, line in enumerate(lines, start=1):
            # Converte a linha em dicionário com os nomes das colunas
            row_dict = dict(zip(columns, line, strict=False))
            buffer.append(row_dict)

            if len(buffer) >= self.insert_buffer_size:
                self._insert_batch(table_name, columns, buffer)
                buffer = []

        if buffer:
            self._insert_batch(table_name, columns, buffer)

        logger.info(
            "Inseridos %s registros na tabela %s",
            count,
            table_name,
            extra={"indentation": 1},
        )

    def populate_unified_table(self):
        """
        Popula a tabela unificada de CEPs.
        
        Para ClickHouse, cria uma view materializada ou tabela derivada
        com os dados unificados.
        """
        logger.info(
            "Preenchendo tabela unificada de CEPs",
            extra={"indentation": 0},
        )
        
        tables_map = self.metadata.info.get("original_name_map", {})
        cep_unificado = tables_map.get("cep_unificado", "cep_unificado")
        log_logradouro = tables_map.get("log_logradouro", "log_logradouro")
        log_bairro = tables_map.get("log_bairro", "log_bairro")
        log_localidade = tables_map.get("log_localidade", "log_localidade")
        log_cpc = tables_map.get("log_cpc", "log_cpc")
        log_grande_usuario = tables_map.get("log_grande_usuario", "log_grande_usuario")
        log_unid_oper = tables_map.get("log_unid_oper", "log_unid_oper")

        # Mantém tabela de destino e insere dados unificados respeitando o schema real do e-DNE.
        unified_sql = f"""
        INSERT INTO {cep_unificado}
        (cep, logradouro, complemento, bairro, municipio, municipio_cod_ibge, uf, nome)
        SELECT
            cep,
            logradouro,
            complemento,
            bairro,
            municipio,
            municipio_cod_ibge,
            uf,
            nome
        FROM (
            SELECT
                ll.cep AS cep,
                if(ll.log_sta_tlo = 'S', concat(ll.tlo_tx, ' ', ll.log_no), ll.log_no) AS logradouro,
                ll.log_complemento AS complemento,
                lb.bai_no AS bairro,
                lc.loc_no AS municipio,
                lc.mun_nu AS municipio_cod_ibge,
                ll.ufe_sg AS uf,
                CAST(NULL, 'Nullable(String)') AS nome
            FROM {log_logradouro} ll
            INNER JOIN {log_localidade} lc ON ll.loc_nu = lc.loc_nu
            INNER JOIN {log_bairro} lb ON ll.bai_nu_ini = lb.bai_nu

            UNION ALL

            SELECT
                lc.cep AS cep,
                CAST(NULL, 'Nullable(String)') AS logradouro,
                CAST(NULL, 'Nullable(String)') AS complemento,
                CAST(NULL, 'Nullable(String)') AS bairro,
                lc.loc_no AS municipio,
                lc.mun_nu AS municipio_cod_ibge,
                lc.ufe_sg AS uf,
                CAST(NULL, 'Nullable(String)') AS nome
            FROM {log_localidade} lc
            WHERE lc.cep IS NOT NULL
              AND lc.loc_nu_sub IS NULL
              AND lc.mun_nu IS NOT NULL

            UNION ALL

            SELECT
                cpc.cep AS cep,
                cpc.cpc_endereco AS logradouro,
                CAST(NULL, 'Nullable(String)') AS complemento,
                CAST(NULL, 'Nullable(String)') AS bairro,
                coalesce(loc_sub.loc_no, loc.loc_no) AS municipio,
                coalesce(loc_sub.mun_nu, loc.mun_nu) AS municipio_cod_ibge,
                cpc.ufe_sg AS uf,
                cpc.cpc_no AS nome
            FROM {log_cpc} cpc
            INNER JOIN {log_localidade} loc ON cpc.loc_nu = loc.loc_nu
            LEFT JOIN {log_localidade} loc_sub ON loc.loc_nu_sub = loc_sub.loc_nu

            UNION ALL

            SELECT
                gru.cep AS cep,
                gru.gru_endereco AS logradouro,
                CAST(NULL, 'Nullable(String)') AS complemento,
                lb.bai_no AS bairro,
                coalesce(loc_sub.loc_no, loc.loc_no) AS municipio,
                coalesce(loc_sub.mun_nu, loc.mun_nu) AS municipio_cod_ibge,
                gru.ufe_sg AS uf,
                gru.gru_no AS nome
            FROM {log_grande_usuario} gru
            INNER JOIN {log_localidade} loc ON gru.loc_nu = loc.loc_nu
            INNER JOIN {log_bairro} lb ON gru.bai_nu = lb.bai_nu
            LEFT JOIN {log_localidade} loc_sub ON loc.loc_nu_sub = loc_sub.loc_nu

            UNION ALL

            SELECT
                uop.cep AS cep,
                uop.uop_endereco AS logradouro,
                CAST(NULL, 'Nullable(String)') AS complemento,
                lb.bai_no AS bairro,
                coalesce(loc_sub.loc_no, loc.loc_no) AS municipio,
                coalesce(loc_sub.mun_nu, loc.mun_nu) AS municipio_cod_ibge,
                uop.ufe_sg AS uf,
                uop.uop_no AS nome
            FROM {log_unid_oper} uop
            INNER JOIN {log_localidade} loc ON uop.loc_nu = loc.loc_nu
            INNER JOIN {log_bairro} lb ON uop.bai_nu = lb.bai_nu
            LEFT JOIN {log_localidade} loc_sub ON loc.loc_nu_sub = loc_sub.loc_nu
            WHERE coalesce(loc_sub.mun_nu, loc.mun_nu) IS NOT NULL
        ) unified_rows
        """
        
        try:
            self._execute(f"TRUNCATE TABLE {cep_unificado}")
            self._execute(unified_sql)
            logger.info(
                "Tabela unificada de CEPs preenchida",
                extra={"indentation": 1},
            )
        except Exception as e:
            logger.error(
                "Erro ao preencher tabela unificada: %s",
                str(e),
                extra={"indentation": 1},
            )
            raise

    def _insert_batch(self, table_name: str, columns: list[str], batch: list[dict]):
        """
        Insere um lote de dados no ClickHouse.
        
        Args:
            table_name: Nome da tabela
            columns: Lista de nomes de colunas
            batch: Lista de dicionários com os dados
        """
        try:
            data = [tuple(row.get(col) for col in columns) for row in batch]

            if self.interface == "native":
                self.client.execute(
                    f"INSERT INTO {table_name} ({', '.join(columns)}) VALUES",
                    data,
                )
            else:
                self.client.insert(table_name, data, column_names=columns)
        except Exception as e:
            logger.error(
                "Erro ao inserir lote em %s: %s",
                table_name,
                str(e),
                extra={"indentation": 2},
            )
            raise

    def _build_create_table_sql(self, table_name: str, table) -> str:
        """
        Constrói a instrução SQL para criar uma tabela no ClickHouse.
        
        Args:
            table_name: Nome da tabela
            table: Objeto Table do SQLAlchemy
            
        Returns:
            String com o SQL CREATE TABLE para ClickHouse
        """
        columns_sql = []
        
        for column in table.columns:
            col_type = self._get_clickhouse_type(column)
            nullable = "Nullable(" + col_type + ")" if column.nullable else col_type
            columns_sql.append(f"{column.name} {nullable}")
        
        # Identifica a chave primária
        pk_columns = [c.name for c in table.primary_key.columns]
        pk_clause = f", PRIMARY KEY ({', '.join(pk_columns)})" if pk_columns else ""
        
        return f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            {', '.join(columns_sql)}
        ) ENGINE = {self.default_engine}
        ORDER BY ({', '.join(pk_columns or ['1'])})
        """

    @staticmethod
    def _get_clickhouse_type(column) -> str:
        """
        Converte tipos de coluna SQLAlchemy para tipos ClickHouse.
        
        Args:
            column: Coluna SQLAlchemy
            
        Returns:
            String com o tipo ClickHouse correspondente
        """
        col_type_str = str(column.type)
        
        # Mapeamento de tipos
        type_mapping = {
            "INTEGER": "Int32",
            "BIGINT": "Int64",
            "SMALLINT": "Int16",
            "VARCHAR": "String",
            "CHAR": "String",
            "TEXT": "String",
            "DATE": "Date",
            "DATETIME": "DateTime",
            "BOOLEAN": "UInt8",
        }
        
        # Procura correspondência no tipo SQLAlchemy
        for sql_type, ch_type in type_mapping.items():
            if sql_type in col_type_str.upper():
                return ch_type
        
        # Trata VARCHAR com tamanho específico
        if "VARCHAR" in col_type_str.upper():
            return "String"
        
        # Padrão: String
        return "String"

    def _execute(self, query: str):
        if self.interface == "native":
            return self.client.execute(query)
        return self.client.command(query)

    @staticmethod
    def _detect_interface(port: int) -> str:
        if port in (8123, 8443):
            return "http"
        return "native"

    @staticmethod
    def _resolve_host_port(host: str, port: int) -> tuple[str, int]:
        host = host.strip()

        if host.startswith("http://") or host.startswith("https://"):
            parsed = urlparse(host)
            resolved_port = parsed.port

            if resolved_port is None:
                resolved_port = 8443 if parsed.scheme == "https" else 8123

            return parsed.hostname or "localhost", resolved_port

        if ":" in host:
            host_part, maybe_port = host.rsplit(":", 1)
            if maybe_port.isdigit():
                return host_part, int(maybe_port)

        return host, port
