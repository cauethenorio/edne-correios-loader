import enum
import logging
from typing import TYPE_CHECKING, Iterable, List, Union

from sqlalchemy import Engine, create_engine

from .specs import LoadableDneTable, loadable_tables
from .tables import metadata

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
    tables_to_populate: List[LoadableDneTable]
    metadata: "MetaData" = metadata

    insert_buffer_size = 1000

    # used to keep track of whether the tables were created or not
    were_tables_created = False

    connection: Union["Connection", None]

    def __init__(
        self,
        database_url: str,
        tables: TablesSetEnum,
    ):
        self.engine = create_engine(database_url, echo=False)

        self.tables_to_populate = [
            t for t in loadable_tables if tables == TablesSetEnum.ALL_TABLES or t.required_for_cep_search
        ]

    def __enter__(self):
        logger.info("Connecting to database...", extra={"indentation": 0})
        self.connection = self.engine.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_val:
            # if something went wrong, rollback and drop the tables
            self.connection.rollback()

            if self.were_tables_created:
                logger.warning("Something went wrong, dropping tables...", extra={"indentation": 0})
                self.drop_tables()
                self.connection.commit()

        else:
            self.connection.commit()

        self.connection.close()

    def drop_tables(self):
        tables = [self.metadata.tables[t.table_name] for t in self.tables_to_populate]
        tables_names = "\n".join([f"- {t.table_name}" for t in self.tables_to_populate])

        logger.debug("Dropping tables (if they exist):\n%s", tables_names)
        metadata.drop_all(self.engine, tables=tables)
        self.were_tables_created = False

        return [tables, tables_names]

    def drop_and_create_tables(self):
        tables, tables_names = self.drop_tables()

        logger.info("Creating tables:\n%s", tables_names, extra={"indentation": 0})
        metadata.create_all(self.engine, tables=tables)
        self.were_tables_created = True

    def populate_table(self, table_name: str, lines: Iterable[list[str]]):
        table = self.metadata.tables[table_name]
        columns = [c.name for c in table.columns]

        self_referencing_fk = self.find_self_referencing_fks(table)

        if self_referencing_fk:
            lines = self.sort_topologically(lines, self_referencing_fk, columns)

        buffer = []

        for count, line in enumerate(lines):  # noqa: B007
            buffer.append(dict(zip(columns, line, strict=True)))

            if len(buffer) > self.insert_buffer_size:
                self.connection.execute(table.insert(), buffer)
                buffer = []

        if buffer:
            self.connection.execute(table.insert(), buffer)

        logger.info('Inserted %s rows into table "%s"', count, table_name, extra={"indentation": 1})

    def populate_unified_table(self):
        pass

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
