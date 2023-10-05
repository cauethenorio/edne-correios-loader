import enum
from typing import List, Union

from .tables import metadata


class TableSetEnum(enum.Enum):
    """
    Options to control which tables to keep in the database after the import.
    """

    UNIFIED_CEP_ONLY = "unified-cep-only"
    CEP_TABLES = "cep-tables"
    ALL_TABLES = "all"

    @property
    def to_populate(self) -> List[str]:
        if self.value == "all":
            return [t.name for t in metadata.sorted_tables]

        return get_cep_tables()

    @property
    def to_drop(self) -> List[str]:
        if self.value == "unified-cep-only":
            return [
                t.name
                for t in metadata.sorted_tables
                if not t.info.get("unified_table")
            ]

        return []


def get_cep_tables() -> List[str]:
    """
    Get the list of tables that are required for CEP search.
    """
    tables = []
    dependencies = set()

    for table in reversed(metadata.sorted_tables):
        if "cep" in table.c or table.name in dependencies:
            for dep in table.foreign_keys:
                dependencies.add(dep.column.table.name)

            tables.append(table.name)

    return list(reversed(tables))


def get_table_files_glob(table_name: str) -> Union[str, None]:
    """
    Get the file globs for each table.
    Calculate from table name when not specified.
    """
    table = metadata.tables[table_name]

    if table.info.get("unified_table", False):
        return None

    return table.info.get("file_glob", f"{table.name.upper()}.TXT")
