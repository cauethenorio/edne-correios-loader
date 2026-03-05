from unittest.mock import sentinel

import pytest
import sqlalchemy as sa

from edne_correios_loader import CepQuerier, DneLoader
from edne_correios_loader.table_set import (
    TableSetEnum,
    get_cep_tables,
    get_table_files_glob,
)
from edne_correios_loader.tables import (
    DEFAULT_TABLE_NAMES,
    build_metadata,
    get_table,
    make_table_name_fn,
)

# --- make_table_name_fn ---


def test_make_table_name_fn_with_none_returns_identity():
    fn = make_table_name_fn(None)
    assert fn("log_localidade") == "log_localidade"


def test_make_table_name_fn_with_dict_maps_known_keys():
    fn = make_table_name_fn({"log_localidade": "my_loc"})
    assert fn("log_localidade") == "my_loc"


def test_make_table_name_fn_with_dict_falls_back_to_original():
    fn = make_table_name_fn({"log_localidade": "my_loc"})
    assert fn("log_bairro") == "log_bairro"


def test_make_table_name_fn_with_callable():
    fn = make_table_name_fn(lambda name: f"dne_{name}")
    assert fn("log_localidade") == "dne_log_localidade"


# --- build_metadata ---


def test_build_metadata_default_uses_original_names():
    metadata = build_metadata()
    table_names = {t.name for t in metadata.sorted_tables}
    assert table_names == set(DEFAULT_TABLE_NAMES)


def test_build_metadata_with_callable_renames_all_tables():
    metadata = build_metadata(lambda name: f"prefix_{name}")
    table_names = {t.name for t in metadata.sorted_tables}

    expected = {f"prefix_{name}" for name in DEFAULT_TABLE_NAMES}
    assert table_names == expected


def test_build_metadata_with_dict_renames_only_specified_tables():
    metadata = build_metadata({"cep_unificado": "my_cep"})
    table_names = {t.name for t in metadata.sorted_tables}

    assert "my_cep" in table_names
    assert "cep_unificado" not in table_names
    assert "log_localidade" in table_names


def test_build_metadata_preserves_original_name_in_info():
    metadata = build_metadata(lambda name: f"prefix_{name}")

    for table in metadata.sorted_tables:
        assert "original_name" in table.info
        assert table.name == f"prefix_{table.info['original_name']}"


def test_build_metadata_foreign_keys_reference_renamed_tables():
    metadata = build_metadata(lambda name: f"x_{name}")

    log_bairro = get_table(metadata, "log_bairro")
    fk_targets = {fk.column.table.name for fk in log_bairro.foreign_keys}

    assert "x_log_localidade" in fk_targets
    assert "log_localidade" not in fk_targets


def test_build_metadata_self_referencing_fk_uses_renamed_table():
    metadata = build_metadata({"log_localidade": "municipios"})

    log_localidade = get_table(metadata, "log_localidade")
    assert log_localidade.name == "municipios"

    self_fks = [
        fk
        for fk in log_localidade.foreign_keys
        if fk.column.table.name == log_localidade.name
    ]
    assert len(self_fks) == 1


# --- get_table ---


def test_get_table_finds_by_original_name():
    metadata = build_metadata({"log_bairro": "bairros"})

    table = get_table(metadata, "log_bairro")
    assert table.name == "bairros"


def test_get_table_raises_for_unknown_original_name():
    metadata = build_metadata()

    with pytest.raises(KeyError, match="nonexistent"):
        get_table(metadata, "nonexistent")


# --- table_set with custom metadata ---


def test_get_cep_tables_with_custom_metadata():
    metadata = build_metadata(lambda name: f"dne_{name}")

    tables = get_cep_tables(metadata)
    assert "dne_cep_unificado" in tables
    assert "cep_unificado" not in tables


def test_table_set_to_populate_with_custom_metadata():
    metadata = build_metadata({"cep_unificado": "my_cep"})

    tables = TableSetEnum.CEP_TABLES.to_populate(metadata)
    assert "my_cep" in tables
    assert "cep_unificado" not in tables


def test_table_set_to_drop_with_custom_metadata():
    metadata = build_metadata({"cep_unificado": "my_cep"})

    tables = TableSetEnum.UNIFIED_CEP_ONLY.to_drop(metadata)
    assert "my_cep" not in tables
    assert all(t != "my_cep" for t in tables)


def test_get_table_files_glob_uses_original_name_for_renamed_tables():
    metadata = build_metadata({"log_faixa_uf": "faixa_uf"})

    assert get_table_files_glob("faixa_uf", metadata) == "LOG_FAIXA_UF.TXT"


def test_get_table_files_glob_preserves_custom_file_glob():
    metadata = build_metadata({"log_logradouro": "logradouros"})

    assert (
        get_table_files_glob("logradouros", metadata) == "LOG_LOGRADOURO_*.TXT"
    )


def test_get_table_files_glob_returns_none_for_unified_table():
    metadata = build_metadata({"cep_unificado": "my_cep"})

    assert get_table_files_glob("my_cep", metadata) is None


# --- DneLoader with custom table names ---


@pytest.fixture
def dne_resolver(mocker):
    mock = mocker.patch(
        "edne_correios_loader.loader.DneLoader.DneResolver"
    )
    mock.return_value.__enter__.return_value = mock.return_value
    return mock


@pytest.fixture
def db_writer(mocker):
    mock = mocker.patch(
        "edne_correios_loader.loader.DneLoader.DneDatabaseWriter"
    )
    mock.return_value.__enter__.return_value = mock.return_value
    return mock


def test_loader_with_dict_table_names_uses_custom_metadata(
    dne_resolver,  # noqa: ARG001
    db_writer,
    mocker,
):
    mocker.patch("edne_correios_loader.loader.TableFilesReader")

    loader = DneLoader(
        sentinel.db_url,
        dne_source=sentinel.dne_source,
        table_names={"cep_unificado": "my_cep"},
    )

    assert get_table(loader.metadata, "cep_unificado").name == "my_cep"

    loader.load()

    tables_created = db_writer.return_value.create_tables.call_args[0][0]
    assert "my_cep" in tables_created
    assert "cep_unificado" not in tables_created


def test_loader_with_callable_table_names_uses_custom_metadata(
    dne_resolver,  # noqa: ARG001
    db_writer,
    mocker,
):
    mocker.patch("edne_correios_loader.loader.TableFilesReader")

    loader = DneLoader(
        sentinel.db_url,
        dne_source=sentinel.dne_source,
        table_names=lambda name: f"dne_{name}",
    )

    assert get_table(loader.metadata, "log_localidade").name == "dne_log_localidade"

    loader.load()

    tables_created = db_writer.return_value.create_tables.call_args[0][0]
    assert all(t.startswith("dne_") for t in tables_created)


def test_loader_without_table_names_uses_defaults(
    dne_resolver,  # noqa: ARG001
    db_writer,
    mocker,
):
    mocker.patch("edne_correios_loader.loader.TableFilesReader")

    loader = DneLoader(sentinel.db_url, dne_source=sentinel.dne_source)
    loader.load()

    tables_created = db_writer.return_value.create_tables.call_args[0][0]
    assert "cep_unificado" in tables_created


# --- CepQuerier with custom table name ---


def test_cep_querier_with_custom_table_name(connection_url):
    custom_metadata = build_metadata({"cep_unificado": "my_cep"})
    cep_table = get_table(custom_metadata, "cep_unificado")

    cep_data = {
        "cep": "99999999",
        "logradouro": None,
        "complemento": None,
        "bairro": None,
        "municipio": "Test City",
        "municipio_cod_ibge": 123456,
        "uf": "SP",
        "nome": None,
    }

    with sa.create_engine(connection_url).connect() as conn:
        custom_metadata.create_all(conn, tables=[cep_table])
        conn.execute(cep_table.insert(), [cep_data])
        conn.commit()

    querier = CepQuerier(connection_url, cep_table_name="my_cep")
    assert querier.query("99999999") == cep_data


def test_cep_querier_without_custom_table_name_uses_default(
    connection_url,
):
    default_metadata = build_metadata()
    cep_table = default_metadata.tables["cep_unificado"]

    cep_data = {
        "cep": "88888888",
        "logradouro": None,
        "complemento": None,
        "bairro": None,
        "municipio": "Default City",
        "municipio_cod_ibge": 654321,
        "uf": "RJ",
        "nome": None,
    }

    with sa.create_engine(connection_url).connect() as conn:
        default_metadata.create_all(conn, tables=[cep_table])
        conn.execute(cep_table.insert(), [cep_data])
        conn.commit()

    querier = CepQuerier(connection_url)
    assert querier.query("88888888") == cep_data
