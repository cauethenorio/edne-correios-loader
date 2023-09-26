import logging
from pathlib import Path
from typing import Iterable, Type

from .dbwriter import DneDatabaseWriter, TablesSetEnum
from .resolver import DneResolver
from .specs import loadable_tables

logger = logging.getLogger(__name__)


class DneLoader:
    DneResolver: Type[DneResolver] = DneResolver
    DneDatabaseWriter: Type[DneDatabaseWriter] = DneDatabaseWriter

    database_url: str
    dne_source: str

    read_buffer_size = 1000000

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
        tables_set: TablesSetEnum = TablesSetEnum.UNIFIED_CEP_ONLY,
    ):
        tables = [
            t.table_name
            for t in loadable_tables
            if tables_set == TablesSetEnum.ALL_TABLES or t.required_for_cep_search
        ]

        # connect to database to ensure the URL is valid
        # connection will be closed when the context manager exits
        with self.DneDatabaseWriter(self.database_url) as database_writer:
            # now that we know the URL is valid, download/extract the DNE file
            # temp files will be removed when the context manager exits
            with self.DneResolver(self.dne_source) as dne_path:
                # all good, let's start by ensuring the tables exist and are empty
                database_writer.create_tables(tables)
                database_writer.clean_tables(tables)

                for table_name in tables:
                    loadable_table = next(
                        t for t in loadable_tables if t.table_name == table_name
                    )

                    # skip cep unified table, it's populated at the end
                    if loadable_table.file_glob == "":
                        continue

                    files = dne_path.glob(loadable_table.file_glob)

                    data = TableFilesReader(files, buffer_size=self.read_buffer_size)
                    database_writer.populate_table(loadable_table.table_name, data)

            database_writer.populate_unified_table()


class TableFilesReader:
    """
    Memory-efficient reader for DNE files targeting a single table.
    Read files sequentially in chunks of lines and yield each line
    """

    def __init__(self, files: Iterable[Path], buffer_size=1000000):
        self.files = files
        self.buffer_size = buffer_size

    def __iter__(self):
        for file in self.files:
            with file.open(encoding="latin1") as fp:
                logger.info("Reading %s", file.name, extra={"indentation": 1})
                lines_buffer = fp.readlines(self.buffer_size)

                while lines_buffer:
                    logger.debug(
                        "Read %s lines from %s",
                        len(lines_buffer),
                        file.name,
                        extra={"indentation": 2},
                    )
                    for line in lines_buffer:
                        yield [f.strip() or None for f in line.split("@")]

                    lines_buffer = fp.readlines(self.buffer_size)
