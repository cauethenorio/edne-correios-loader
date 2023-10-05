from unittest.mock import sentinel

import pytest

from dne_correios_loader import DneLoader
from dne_correios_loader.loader import TableFilesReader
from dne_correios_loader.table_set import TableSetEnum


db_url = sentinel.database_url
dne_source = sentinel.dne_source


@pytest.fixture
def dne_resolver(mocker):
    mock = mocker.patch("dne_correios_loader.loader.DneLoader.DneResolver")
    mock.return_value.__enter__.return_value = mock.return_value
    return mock


@pytest.fixture
def db_writer(mocker):
    mock = mocker.patch("dne_correios_loader.loader.DneLoader.DneDatabaseWriter")
    mock.return_value.__enter__.return_value = mock.return_value
    return mock


@pytest.mark.parametrize(
    "table_set",
    [
        TableSetEnum.UNIFIED_CEP_ONLY,
        TableSetEnum.CEP_TABLES,
        TableSetEnum.ALL_TABLES,
    ],
)
def test_loader_create_populate_and_drop_correct_tables(
    table_set, dne_resolver, db_writer, mocker
):
    table_files_reader = mocker.patch("dne_correios_loader.loader.TableFilesReader")
    loader = DneLoader(db_url, dne_source=dne_source)
    loader.load(table_set=table_set)

    db_writer.return_value.create_tables.assert_called_once_with(table_set.to_populate)
    db_writer.return_value.drop_tables.assert_called_once_with(table_set.to_drop)

    assert db_writer.return_value.populate_table.call_args_list == [
        mocker.call(table_name, table_files_reader.return_value)
        for table_name in table_set.to_populate
        if table_name != "cep_unificado"
    ]

    db_writer.return_value.populate_unified_table.assert_called_once_with()


def test_table_files_reader(temporary_dne_dir):
    logradouros_sp = [
        [
            "98",
            "AC",
            "16",
            "29",
            None,
            "Bom Destino",
            None,
            "69918306",
            "Rua",
            "S",
            "R Bom Destino",
        ],
        [
            "987346",
            "AC",
            "16",
            "32",
            None,
            "José Augusto",
            None,
            "69900821",
            "Travessa",
            "S",
            "Tv José Augusto",
        ],
    ]

    logradouros_al = [
        [
            "995",
            "AL",
            "30",
            "63",
            None,
            "Coronel Ataíde de Oliveira",
            None,
            "57313710",
            "Rua",
            "S",
            "R Cel Ataíde de Oliveira",
        ],
        [
            "997",
            "AL",
            "30",
            "61",
            None,
            "Coronel José de Farias",
            None,
            "57305480",
            "Praça",
            "S",
            "Pç Cel José de Farias",
        ],
    ]

    temporary_dne_dir.populate_file("LOG_LOGRADOURO_SP.TXT", logradouros_sp)
    temporary_dne_dir.populate_file("LOG_LOGRADOURO_AL.TXT", logradouros_al)
    files = temporary_dne_dir.innerdir.glob("LOG_LOGRADOURO_*.TXT")

    assert list(TableFilesReader(files)) == logradouros_sp + logradouros_al
