import json
import logging
import sys
from typing import Optional

import click

from edne_correios_loader.__about__ import __version__
from edne_correios_loader.cep_querier import CepQuerier
from edne_correios_loader.dbwriter import logger as dbwriter_logger
from edne_correios_loader.loader import DneLoader
from edne_correios_loader.loader import logger as loader_logger
from edne_correios_loader.resolver import DneResolver
from edne_correios_loader.resolver import logger as resolver_logger
from edne_correios_loader.table_set import TableSetEnum
from edne_correios_loader.unified_table import logger as unified_table_logger

from .logger import add_verbose_option

logger = logging.getLogger(__name__)


class DneResolverWithDownloadProgress(DneResolver):
    progress_bar: Optional[click.progressbar] = None

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
@add_verbose_option(
    [logger, loader_logger, resolver_logger, dbwriter_logger, unified_table_logger]
)
def load(dne_source, database_url, tables, verbose):
    """
    Load DNE data into a database.
    """

    click.echo(click.style(f"Starting DNE Correios Loader v{__version__}", bold=True))

    try:
        DneLoaderWithProgress(database_url, dne_source=dne_source).load(
            table_set=TableSetEnum(tables)
        )
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
@click.argument("cep")
@edne_correios_loader.command()
def query_cep(database_url, cep):
    """
    Query a CEP from the database to ensure it was correctly populated.
    """
    try:
        cep_address = CepQuerier(database_url).query(cep)
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
