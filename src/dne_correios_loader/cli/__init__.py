import logging
import sys
from typing import Optional

import click

from dne_correios_loader.__about__ import __version__
from dne_correios_loader.dbwriter import logger as dbwriter_logger
from dne_correios_loader.loader import DneLoader, TablesSetEnum
from dne_correios_loader.loader import logger as loader_logger
from dne_correios_loader.resolver import DneResolver
from dne_correios_loader.resolver import logger as resolver_logger
from dne_correios_loader.unified_table import logger as unified_table_logger

from .logger import add_verbose_option

logger = logging.getLogger(__name__)


class DneResolverWithDownloadProgress(DneResolver):
    progress_bar: Optional[click.progressbar] = None

    def download_dne(self, url: str) -> str:
        path = super().download_dne(url)
        self.progress_bar.render_finish()
        return path

    def download_report_hook(self, _, bs, size):
        if self.progress_bar is None:
            self.progress_bar = click.progressbar(
                length=size, label="Downloading DNE file"
            )

        self.progress_bar.update(bs)


class DneLoaderWithProgress(DneLoader):
    DneResolver = DneResolverWithDownloadProgress


@click.group(context_settings={"help_option_names": ["-h", "--help"]})
@click.version_option(version=__version__, prog_name="DNE Correios Loader")
def dne_correios_loader():
    ...


@dne_correios_loader.command()
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
        [option.value for option in list(TablesSetEnum)],
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
            tables_set=TablesSetEnum(tables),
        )
    except Exception as e:
        if verbose:
            logger.exception(e)  # noqa: TRY401
        else:
            logger.error(e)  # noqa: TRY400

        sys.exit(1)


@dne_correios_loader.command()
def query_cep():
    """
    Query a CEP from the database.
    """
    click.echo("query cep")
