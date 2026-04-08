from __future__ import annotations

import json
import logging
import sys

import click

from edne_correios_loader.__about__ import __version__
from edne_correios_loader.cep_querier import CepQuerier
from edne_correios_loader.clickhouse_writer import ClickHouseWriter
from edne_correios_loader.clickhouse_writer import logger as clickhouse_logger
from edne_correios_loader.dbwriter import logger as dbwriter_logger
from edne_correios_loader.loader import DneLoader
from edne_correios_loader.loader import logger as loader_logger
from edne_correios_loader.loader import TableFilesReader
from edne_correios_loader.resolver import DneResolver
from edne_correios_loader.resolver import logger as resolver_logger
from edne_correios_loader.table_set import TableSetEnum, get_table_files_glob
from edne_correios_loader.tables import DEFAULT_TABLE_NAMES, build_metadata
from edne_correios_loader.unified_table import logger as unified_table_logger

from .logger import add_verbose_option

logger = logging.getLogger(__name__)


class DneResolverWithDownloadProgress(DneResolver):
    progress_bar: click.progressbar | None = None

    def download_report_hook(self, read, total, hook_type):
        if total == -1:
            return

        if hook_type == "start":
            self.progress_bar = click.progressbar(
                length=total, label="Downloading DNE file"
            )
            self.progress_bar.render_progress()

        if read:
            self.progress_bar.update(read)

        if hook_type == "finish":
            self.progress_bar.finish()
            self.progress_bar.render_finish()


class DneLoaderWithProgress(DneLoader):
    DneResolver = DneResolverWithDownloadProgress


class TableNameParamType(click.ParamType):
    """
    Click parameter type for --table-name key=value pairs.
    """

    name = "key=value"

    def convert(self, value, param, ctx):
        if "=" not in value:
            self.fail(
                f"Expected format 'original=custom', got '{value}'",
                param,
                ctx,
            )

        key, _, custom = value.partition("=")
        key = key.strip()
        custom = custom.strip()

        if not key or not custom:
            self.fail(
                f"Expected format 'original=custom', got '{value}'",
                param,
                ctx,
            )

        if key not in DEFAULT_TABLE_NAMES:
            self.fail(
                f"Unknown table name '{key}'. "
                f"Valid names: {', '.join(DEFAULT_TABLE_NAMES)}",
                param,
                ctx,
            )

        return (key, custom)


def parse_table_names(table_name):
    """
    Build table name mapping from --table-name pairs.
    """
    if not table_name:
        return None

    return dict(table_name)


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="DNE Correios Loader")
def edne_correios_loader(): ...  # pragma: no cover


@edne_correios_loader.command()
@click.option(
    "-s",
    "--dne-source",
    help="Path or URL with the DNE file/dir to be imported",
    metavar="<path/zip-file/url>",
)
@click.option(
    "-db",
    "--database-url",
    help="Database URL where the DNE data will be imported to",
    required=True,
    metavar="<url>",
)
@click.option(
    "--tables",
    type=click.Choice(
        [option.value for option in list(TableSetEnum)],
        case_sensitive=False,
    ),
    help="Which tables to keep in the database after the import",
    default="unified-cep-only",
)
@click.option(
    "--table-name",
    type=TableNameParamType(),
    multiple=True,
    help="Rename a table: --table-name original=custom",
    metavar="<original=custom>",
)
@add_verbose_option(
    [logger, loader_logger, resolver_logger, dbwriter_logger, unified_table_logger]
)
def load(dne_source, database_url, tables, table_name, verbose):
    """
    Load DNE data into a database.
    """

    click.echo(click.style(f"Starting DNE Correios Loader v{__version__}", bold=True))

    try:
        table_names = parse_table_names(table_name)

        DneLoaderWithProgress(
            database_url, dne_source=dne_source, table_names=table_names
        ).load(table_set=TableSetEnum(tables))
    except Exception as e:
        if verbose:
            logger.exception(e)  # noqa: TRY401
        else:
            logger.error(e)  # noqa: TRY400

        sys.exit(1)


@click.option(
    "-db",
    "--database-url",
    help="Database URL where the DNE data will be imported to",
    required=True,
    metavar="<url>",
)
@click.option(
    "--cep-table-name",
    help="Custom name for the unified CEP table",
    metavar="<name>",
)
@click.argument("cep")
@edne_correios_loader.command()
def query_cep(database_url, cep_table_name, cep):
    """
    Query a CEP from the database to ensure it was correctly populated.
    """
    try:
        cep_address = CepQuerier(database_url, cep_table_name=cep_table_name).query(cep)
    except Exception as e:
        logger.error(e)  # noqa: TRY400
        sys.exit(1)

    if cep_address:
        click.echo(
            click.style(
                json.dumps(cep_address, ensure_ascii=False, indent=2), fg="green"
            )
        )
    else:
        click.echo(click.style("CEP not found", fg="blue"), err=True)
        sys.exit(3)


@edne_correios_loader.command()
@click.option(
    "-s",
    "--dne-source",
    help="Caminho ou URL com arquivo/diretório e-DNE a ser importado",
    metavar="<path/zip-file/url>",
)
@click.option(
    "-ch",
    "--clickhouse-host",
    help="Host do servidor ClickHouse (aceita host:porta)",
    default="localhost",
    metavar="<host>",
)
@click.option(
    "-cp",
    "--clickhouse-port",
    help="Porta do servidor ClickHouse",
    default=9000,
    type=int,
    metavar="<port>",
)
@click.option(
    "-cdb",
    "--clickhouse-database",
    help="Nome do banco de dados no ClickHouse",
    default="default",
    metavar="<database>",
)
@click.option(
    "-cu",
    "--clickhouse-user",
    help="Usuário para autenticação no ClickHouse",
    default="default",
    metavar="<user>",
)
@click.option(
    "-cpw",
    "--clickhouse-password",
    help="Senha para autenticação no ClickHouse",
    default="",
    metavar="<password>",
)
@click.option(
    "--tables",
    type=click.Choice(
        [option.value for option in list(TableSetEnum)],
        case_sensitive=False,
    ),
    help="Quais tabelas manter no banco de dados após a importação",
    default="unified-cep-only",
)
@click.option(
    "--table-name",
    type=TableNameParamType(),
    multiple=True,
    help="Renomear uma tabela: --table-name original=custom",
    metavar="<original=custom>",
)
@add_verbose_option(
    [
        logger,
        loader_logger,
        resolver_logger,
        dbwriter_logger,
        unified_table_logger,
        clickhouse_logger,
    ]
)
def sync_clickhouse(
    dne_source,
    clickhouse_host,
    clickhouse_port,
    clickhouse_database,
    clickhouse_user,
    clickhouse_password,
    tables,
    table_name,
    verbose,
):
    """
    Carrega dados do e-DNE direto para um banco ClickHouse.
    """

    click.echo(
        click.style(
            f"Iniciando DNE Correios Loader v{__version__} → ClickHouse",
            bold=True,
        )
    )

    try:
        table_names = parse_table_names(table_name)
        metadata = build_metadata(table_names)

        with ClickHouseWriter(
            host=clickhouse_host,
            port=clickhouse_port,
            database=clickhouse_database,
            user=clickhouse_user,
            password=clickhouse_password,
            metadata=metadata,
        ) as ch_writer:
            
            with DneResolver(dne_source) as dne_path:
                tables_to_populate = TableSetEnum(tables).to_populate(metadata)
                tables_to_drop = TableSetEnum(tables).to_drop(metadata)

                ch_writer.create_tables(tables_to_populate)
                ch_writer.clean_tables(tables_to_populate)

                for table in tables_to_populate:
                    files_glob = get_table_files_glob(table, metadata)
                    if files_glob:
                        files = dne_path.glob(files_glob)
                        data = TableFilesReader(files)
                        ch_writer.populate_table(table, data)

                ch_writer.populate_unified_table()
                ch_writer.drop_tables(tables_to_drop)

        click.echo(
            click.style(
                "✓ Dados carregados com sucesso no ClickHouse!",
                fg="green",
                bold=True,
            )
        )

    except Exception as e:
        if verbose:
            logger.exception(e)  # noqa: TRY401
        else:
            logger.error(e)  # noqa: TRY400

        sys.exit(1)
