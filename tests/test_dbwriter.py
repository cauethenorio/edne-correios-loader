import pytest
import sqlalchemy as sa

from edne_correios_loader import TableSetEnum
from edne_correios_loader.dbwriter import DneDatabaseWriter
from edne_correios_loader.tables import log_bairro, log_localidade, log_logradouro


def reflect_metadata(engine):
    metadata = sa.MetaData()
    metadata.reflect(bind=engine)
    return metadata


def create_external_tables(engine):
    metadata = sa.MetaData()
    sa.Table("table1", metadata, sa.Column("id", sa.Integer, primary_key=True))
    sa.Table("table2", metadata, sa.Column("id", sa.Integer, primary_key=True))
    metadata.create_all(engine)
    return list(metadata.tables)


def fetch_all(conn, table):
    pks = [c.name for c in table.primary_key]
    return conn.execute(table.select().order_by(*pks)).fetchall()


@pytest.mark.parametrize(
    "table_set,final_tables",
    (
        (TableSetEnum.ALL_TABLES, TableSetEnum.ALL_TABLES.to_populate),
        (TableSetEnum.CEP_TABLES, TableSetEnum.CEP_TABLES.to_populate),
        (TableSetEnum.UNIFIED_CEP_ONLY, ["cep_unificado"]),
    ),
)
def test_dbwriter_create_and_drop_correct_tables(
    connection_url, table_set, final_tables
):
    """
    Ensure that the database writer creates and drops the correct tables and don't
    touch any external table.
    """
    engine = sa.create_engine(connection_url)
    external_tables = create_external_tables(engine)

    with DneDatabaseWriter(connection_url) as db_writer:
        db_writer.create_tables(table_set.to_populate)

        reflected_metadata = reflect_metadata(db_writer.engine)
        existing_tables = set(list(reflected_metadata.tables) + external_tables)

        assert existing_tables == set(table_set.to_populate + external_tables)

        db_writer.drop_tables(table_set.to_drop)
        db_writer.connection.commit()

        reflected_metadata = reflect_metadata(db_writer.engine)
        existing_tables = set(list(reflected_metadata.tables) + external_tables)
        assert existing_tables == set(final_tables + external_tables)


def test_dbwriter_rollback_changes_on_error(
    connection_url, generate_localidades, stringify_row
):
    localidades = generate_localidades(10)

    with DneDatabaseWriter(connection_url) as db_writer:
        db_writer.create_tables(TableSetEnum.CEP_TABLES.to_populate)

        db_writer.populate_table(
            "log_localidade", [stringify_row(row) for row in localidades]
        )

    with pytest.raises(TypeError), DneDatabaseWriter(connection_url) as db_writer:
        db_writer.clean_tables(["log_localidade"])

        rows = db_writer.connection.execute(log_localidade.select()).fetchall()
        assert len(rows) == 0

        msg = "Some unexpected error"
        raise TypeError(msg)

    with sa.create_engine(connection_url).connect() as connection:
        results = connection.execute(
            log_localidade.select().order_by(log_localidade.c.loc_nu)
        ).fetchall()

    assert results == localidades


def test_dbwriter_populate_tables_correctly(
    connection_url,
    generate_bairros,
    generate_localidades,
    generate_logradouros,
    stringify_row,
):
    localidades = generate_localidades(10)
    bairros = generate_bairros(10, localidades)
    logradouros = generate_logradouros(10, localidades, bairros)

    with DneDatabaseWriter(connection_url) as db_writer:
        # test inserting in batches
        db_writer.create_tables(TableSetEnum.CEP_TABLES.to_populate)

        db_writer.insert_buffer_size = 10
        db_writer.populate_table(
            "log_localidade", [stringify_row(l) for l in localidades]
        )

        db_writer.insert_buffer_size = 5
        db_writer.populate_table("log_bairro", [stringify_row(b) for b in bairros])

        db_writer.insert_buffer_size = 3
        db_writer.populate_table(
            "log_logradouro", [stringify_row(l) for l in logradouros]
        )

    with sa.create_engine(connection_url).connect() as connection:
        assert fetch_all(connection, log_localidade) == localidades
        assert fetch_all(connection, log_bairro) == bairros
        assert fetch_all(connection, log_logradouro) == logradouros


def test_dbwriter_is_able_to_populate_tables_with_fk_to_self(
    connection_url, generate_localidades, stringify_row
):
    localidades = generate_localidades(5)

    # turn tuples into lists so we can modify them
    localidades = [list(r) for r in localidades]

    # make localidade #0 a child of localidade #1
    localidades[0][6] = localidades[1][0]

    # make localidade #1 a child of localidade #2
    localidades[1][6] = localidades[2][0]

    # make localidade #3 child of localidade #0
    localidades[3][6] = localidades[0][0]

    with DneDatabaseWriter(connection_url) as db_writer:
        db_writer.create_tables(TableSetEnum.CEP_TABLES.to_populate)

        db_writer.populate_table(
            "log_localidade", [stringify_row(l) for l in localidades]
        )

    with sa.create_engine(connection_url).connect() as connection:
        localidades = [tuple(r) for r in localidades]
        assert fetch_all(connection, log_localidade) == localidades


def test_dbwriter_clean_tables_correctly(
    connection_url,
    generate_bairros,
    generate_localidades,
    generate_logradouros,
    stringify_row,
):
    localidades = generate_localidades(10)
    bairros = generate_bairros(10, localidades)
    logradouros = generate_logradouros(10, localidades, bairros)

    with DneDatabaseWriter(connection_url) as db_writer:
        # test inserting in batches
        db_writer.create_tables(TableSetEnum.CEP_TABLES.to_populate)

        db_writer.insert_buffer_size = 10
        db_writer.populate_table(
            "log_localidade", [stringify_row(l) for l in localidades]
        )

        db_writer.insert_buffer_size = 5
        db_writer.populate_table("log_bairro", [stringify_row(b) for b in bairros])

        db_writer.insert_buffer_size = 3
        db_writer.populate_table(
            "log_logradouro", [stringify_row(l) for l in logradouros]
        )

    with DneDatabaseWriter(connection_url) as db_writer:
        db_writer.clean_tables(TableSetEnum.CEP_TABLES.to_populate)

    with sa.create_engine(connection_url).connect() as connection:
        assert fetch_all(connection, log_localidade) == []
        assert fetch_all(connection, log_bairro) == []
        assert fetch_all(connection, log_logradouro) == []


def test_dbwriter_calls_populate_unified_table(mocker, connection_url):
    populate_unified_table = mocker.patch(
         "edne_correios_loader.dbwriter.populate_unified_table"
    )

    with DneDatabaseWriter(connection_url) as db_writer:
        db_writer.populate_unified_table()
        populate_unified_table.assert_called_once_with(db_writer.connection)
