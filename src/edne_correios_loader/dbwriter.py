import logging
from typing import Iterable, List, Union

import sqlalchemy as sa

from .tables import metadata
from .unified_table import populate_unified_table

logger = logging.getLogger(__name__)


class DneDatabaseWriter:
    engine: sa.Engine
    connection: sa.Connection
    metadata: sa.MetaData = metadata
    insert_buffer_size = 1000

    def __init__(self, database_url: str):
        self.engine = sa.create_engine(database_url, echo=False)

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
                sa.select(sa.func.count()).select_from(table)
            ).scalar():
                logger.info(
                    "Deleting %s rows from table %s",
                    num_rows,
                    table.name,
                    extra={"indentation": 1},
                )
                self.connection.execute(table.delete())

    def drop_tables(self, tables: List[str]):
        if tables:
            logger.info("Dropping tables", extra={"indentation": 0})

            for table in reversed(tables):
                logger.info("Dropping table %s", table, extra={"indentation": 1})
                self.metadata.tables[table].drop(self.connection, checkfirst=True)

    def populate_table(self, table_name: str, lines: Iterable[List[str]]):
        logger.info("Populating table %s", table_name, extra={"indentation": 0})
        table = self.metadata.tables[table_name]
        columns = [c.name for c in table.columns]

        self_referencing_fk = self.find_self_referencing_fks(table)

        if self_referencing_fk:
            # if the table has a self-referencing foreign key, the rows
            # need to be sorted in a way the ancestors are inserted first
            lines = self.sort_topologically(lines, self_referencing_fk, columns)

        buffer = []

        for count, line in enumerate(lines, start=1):  # noqa: B007
            buffer.append(dict(zip(columns, line)))

            if len(buffer) >= self.insert_buffer_size:
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
        lines: Iterable[List[str]], self_referencing_fk: str, columns: List[str]
    ) -> Iterable[List[str]]:
        try:
            from graphlib import TopologicalSorter

            def sorter(graph):
                return tuple(TopologicalSorter(graph).static_order())

        except ImportError:
            from toposort import toposort_flatten

            sorter = toposort_flatten

        fk_index = columns.index(self_referencing_fk)

        # convert iterable to list as it will be iterated multiple times
        lines = list(lines)

        topological_graph = {}

        for line in lines:
            topological_graph.setdefault(line[0], set()).add(line[fk_index])

        sorted_map = sorter(topological_graph)
        return sorted(lines, key=lambda line: sorted_map.index(line[0]))
