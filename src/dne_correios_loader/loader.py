import logging
from pathlib import Path
from typing import Iterable, Type

from .dbwriter import DneDatabaseWriter, TablesSetEnum
from .resolver import DneResolver

logger = logging.getLogger(__name__)


class DneLoader:
    DneResolver: Type[DneResolver] = DneResolver
    DneDatabaseWriter: Type[DneDatabaseWriter] = DneDatabaseWriter

    database_url: str
    dne_source: str

    read_buffer_size = 1000

    def __init__(
        self,
        database_url: str,
        *,
        dne_source: str | None = None,
    ):
        self.database_url = database_url
        self.dne_source = dne_source

    def load(
        self,
        *,
        tables: TablesSetEnum = TablesSetEnum.UNIFIED_CEP_ONLY,
    ):
        # connect to database to ensure the URL is valid
        # connection will be closed when the context manager exits
        with self.DneDatabaseWriter(self.database_url, tables) as database_writer:
            # now that we know the URL is valid, download/extract the DNE file
            # temp files will be removed when the context manager exits
            with self.DneResolver(self.dne_source) as dne_path:
                # all good, let's start by ensuring the tables exist and are empty
                database_writer.drop_and_create_tables()

                for table in database_writer.tables_to_populate:
                    logger.info("Populating table %s", table.table_name, extra={"indentation": 0})
                    files = dne_path.glob(table.file_glob)
                    data = TableFilesReader(files, buffer_size=self.read_buffer_size)

                    database_writer.populate_table(table.table_name, data)

            database_writer.populate_unified_table()


class TableFilesReader:
    """
    Memory-efficient reader for DNE files targeting a single table.
    Read files sequentially in chunks of lines and yield each line
    """

    def __init__(self, files: Iterable[Path], buffer_size=1000):
        self.files = files
        self.buffer_size = buffer_size

    def __iter__(self):
        for file in self.files:
            with file.open(encoding="latin1") as fp:
                logger.info("Reading %s...", file.name, extra={"indentation": 1})
                lines_buffer = fp.readlines(self.buffer_size)

                while lines_buffer:
                    for line in lines_buffer:
                        yield [f.strip() or None for f in line.split("@")]

                    lines_buffer = fp.readlines(self.buffer_size)
