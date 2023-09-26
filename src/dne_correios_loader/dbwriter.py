import enum
import logging
from typing import TYPE_CHECKING, Iterable, List, Union

from sqlalchemy import Engine, create_engine, func, select

from .tables import metadata
from .unified_table import populate_unified_table

if TYPE_CHECKING:
    from sqlalchemy import Connection, MetaData

logger = logging.getLogger(__name__)


class TablesSetEnum(enum.Enum):
    """
    Options to control which tables to keep in the database after the import.
    """

    UNIFIED_CEP_ONLY = "unified-cep-only"
    CEP_TABLES = "cep-tables"
    ALL_TABLES = "all"


class DneDatabaseWriter:
    engine: "Engine"
    metadata: "MetaData" = metadata

    insert_buffer_size = 1000

    connection: Union["Connection", None]

    def __init__(
        self,
        database_url: str,
        # tables: TablesSetEnum,
    ):
        self.engine = create_engine(database_url, echo=False)

    def __enter__(self):
        logger.info("Connecting to database...", extra={"indentation": 0})
        self.connection = self.engine.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            # if something went wrong, rollback all the changes
            self.connection.rollback()

        else:
            self.connection.commit()

        self.connection.close()

    def create_tables(self, tables: List[str]):
        metadata_tables = [self.metadata.tables[t] for t in tables]
        tables_names = "\n".join([f"- {t}" for t in tables])

        logger.info("Creating tables:\n%s", tables_names, extra={"indentation": 0})
        metadata.create_all(self.engine, tables=metadata_tables)

    def clean_tables(self, tables: List[str]):
        logger.info("Cleaning tables", extra={"indentation": 0})

        # delete rows in reverse order to avoid foreign key constraint violations
        for table_name in reversed(tables):
            table = self.metadata.tables[table_name]

            if num_rows := self.connection.execute(
                select(func.count()).select_from(table)
            ).scalar():
                logger.info(
                    "Deleting %s rows from table %s",
                    num_rows,
                    table.name,
                    extra={"indentation": 1},
                )
                self.connection.execute(table.delete())

    def populate_table(self, table_name: str, lines: Iterable[list[str]]):
        logger.info("Populating table %s", table_name, extra={"indentation": 0})
        table = self.metadata.tables[table_name]
        columns = [c.name for c in table.columns]

        self_referencing_fk = self.find_self_referencing_fks(table)

        if self_referencing_fk:
            # if the table has a self-referencing foreign key, the rows
            # need to be sorted in a way the ancestors are inserted first
            lines = self.sort_topologically(lines, self_referencing_fk, columns)

        buffer = []

        for count, line in enumerate(lines):  # noqa: B007
            buffer.append(dict(zip(columns, line, strict=True)))

            if len(buffer) > self.insert_buffer_size:
                self.connection.execute(table.insert(), buffer)
                buffer = []

        if buffer:
            self.connection.execute(table.insert(), buffer)

        logger.info(
            'Inserted %s rows into table "%s"',
            count,
            table_name,
            extra={"indentation": 1},
        )

    def populate_unified_table(self):
        logger.info("Populating unified CEP table", extra={"indentation": 0})
        populate_unified_table(self.connection)

    @staticmethod
    def find_self_referencing_fks(table) -> Union[str, None]:
        """
        Find any column that references the same table.
        If there is one, the rows must be topologically sorted before inserting.
        """
        for fk in list(table.foreign_keys):
            if fk.column.table.name == table.key:
                return fk.parent.name
        return None

    @staticmethod
    def sort_topologically(
        lines: Iterable[list[str]], self_referencing_fk: str, columns: list[str]
    ) -> Iterable[list[str]]:
        from graphlib import TopologicalSorter

        fk_index = columns.index(self_referencing_fk)

        # convert iterable to list as it will be iterated multiple times
        lines = list(lines)

        topological_graph = {}

        for line in lines:
            topological_graph.setdefault(line[0], set()).add(line[fk_index])

        sorted_map = tuple(TopologicalSorter(topological_graph).static_order())
        return sorted(lines, key=lambda line: sorted_map.index(line[0]))
