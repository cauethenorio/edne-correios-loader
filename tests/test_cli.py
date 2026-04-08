import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from edne_correios_loader.cli import (
    DneResolverWithDownloadProgress,
    edne_correios_loader,
    load,
    query_cep,
    sync_clickhouse,
)
from edne_correios_loader.table_set import TableSetEnum

from .shared import create_inner_dne_zip_file


@pytest.fixture
def mocked_dne_loader(mocker):
    return mocker.patch("edne_correios_loader.cli.DneLoaderWithProgress")


@pytest.fixture
def mocked_cep_querier(mocker):
    return mocker.patch("edne_correios_loader.cli.CepQuerier")


@pytest.fixture
def inner_dne_zip_content() -> bytes:
    with create_inner_dne_zip_file() as path:
        yield Path(path).read_bytes()


def test_cli_dner_resolver_with_download_progress_create_progress_bar(
    mock_urlopen, inner_dne_zip_content
):
    with mock_urlopen(inner_dne_zip_content) as url:
        resolver = DneResolverWithDownloadProgress(url)
        with resolver as dne_dir:
            assert Path(dne_dir / "LOG_LOCALIDADE.TXT").is_file()
            assert resolver.progress_bar.finished is True


def test_cli_dner_resolver_with_download_progress_works_without_content_length(
    mock_urlopen, inner_dne_zip_content
):
    with mock_urlopen(inner_dne_zip_content, with_content_length=False) as url:
        resolver = DneResolverWithDownloadProgress(url)
        with resolver as dne_dir:
            assert Path(dne_dir / "LOG_LOCALIDADE.TXT").is_file()
            assert getattr(resolver, "progress_bar", None) is None


def test_cli_show_help_message_when_no_subcommand_is_specified():
    runner = CliRunner()
    result = runner.invoke(edne_correios_loader)

    assert result.exit_code == 2
    assert "Usage: " in result.output


def test_cli_load_command_without_arguments_asks_for_db_url():
    runner = CliRunner()
    result = runner.invoke(load)

    assert result.exit_code == 2
    assert "Error: Missing option '-db' / '--database-url'." in result.output


def test_cli_load_command_accepts_use_default_options(mocked_dne_loader):
    db_url = "db-url-here"

    runner = CliRunner()
    result = runner.invoke(load, ["-db", db_url])

    mocked_dne_loader.assert_called_once_with(db_url, dne_source=None, table_names=None)
    mocked_dne_loader.return_value.load.assert_called_once_with(
        table_set=TableSetEnum.UNIFIED_CEP_ONLY
    )

    assert result.exit_code == 0


def test_cli_load_command_show_error_stack_when_verbose(mocked_dne_loader):
    db_url = "db-url-here"
    exc = Exception("some nasty error")

    mocked_dne_loader.return_value.load.side_effect = exc

    runner = CliRunner()
    result = runner.invoke(load, ["-db", db_url, "--verbose"])

    assert result.exit_code == 1
    assert result.stderr.startswith("ERROR: some nasty error\nTraceback")

    result = runner.invoke(load, ["-db", db_url])
    assert result.exit_code == 1
    assert result.stderr.strip() == "ERROR: some nasty error"


def test_cli_load_command_use_provided_options(mocked_dne_loader):
    db_url = "db-url-here"
    dne_source = "dne-source-here"
    table_set = TableSetEnum.CEP_TABLES

    runner = CliRunner()
    result = runner.invoke(
        load, ["-db", db_url, "--tables", table_set.value, "--dne-source", dne_source]
    )

    assert result.exit_code == 0
    mocked_dne_loader.assert_called_once_with(
        db_url, dne_source=dne_source, table_names=None
    )
    mocked_dne_loader.return_value.load.assert_called_once_with(table_set=table_set)


def test_cli_load_with_single_table_name(mocked_dne_loader):
    runner = CliRunner()
    result = runner.invoke(
        load,
        ["-db", "db-url", "--table-name", "cep_unificado=my_cep"],
    )

    assert result.exit_code == 0
    mocked_dne_loader.assert_called_once_with(
        "db-url",
        dne_source=None,
        table_names={"cep_unificado": "my_cep"},
    )


def test_cli_load_with_multiple_table_names(mocked_dne_loader):
    runner = CliRunner()
    result = runner.invoke(
        load,
        [
            "-db",
            "db-url",
            "--table-name",
            "cep_unificado=my_cep",
            "--table-name",
            "log_localidade=my_loc",
        ],
    )

    assert result.exit_code == 0
    mocked_dne_loader.assert_called_once_with(
        "db-url",
        dne_source=None,
        table_names={"cep_unificado": "my_cep", "log_localidade": "my_loc"},
    )


def test_cli_load_table_name_rejects_invalid_format():
    runner = CliRunner()

    result = runner.invoke(load, ["-db", "db-url", "--table-name", "no_equals"])
    assert result.exit_code == 2
    assert "Expected format" in result.output

    result = runner.invoke(load, ["-db", "db-url", "--table-name", "=value"])
    assert result.exit_code == 2
    assert "Expected format" in result.output

    result = runner.invoke(load, ["-db", "db-url", "--table-name", "key="])
    assert result.exit_code == 2
    assert "Expected format" in result.output


def test_cli_load_table_name_rejects_unknown_table():
    runner = CliRunner()
    result = runner.invoke(load, ["-db", "db-url", "--table-name", "nonexistent=foo"])

    assert result.exit_code == 2
    assert "Unknown table name" in result.output


def test_cli_query_cep_command_asks_for_required_arguments():
    runner = CliRunner()

    result = runner.invoke(query_cep)
    assert result.exit_code == 2
    assert "Error: Missing argument 'CEP'" in result.stderr

    result = runner.invoke(query_cep, ["12345678"])
    assert result.exit_code == 2
    assert "Missing option '-db' / '--database-url'" in result.stderr

    result = runner.invoke(query_cep, ["-db", "db-url"])
    assert result.exit_code == 2
    assert "Error: Missing argument 'CEP'." in result.stderr


def test_cli_query_cep_uses_args_correctly(mocked_cep_querier):
    db_url = "db-url-here"
    cep = "01319-010"
    address = {"rua": "dos bobos"}
    mocked_cep_querier.return_value.query.return_value = address

    runner = CliRunner()
    result = runner.invoke(query_cep, ["--database-url", db_url, cep])
    assert result.exit_code == 0
    assert json.loads(result.stdout) == address
    mocked_cep_querier.return_value.query.assert_called_once_with(cep)

    mocked_cep_querier.return_value.query.return_value = None
    mocked_cep_querier.return_value.query.reset_mock()
    result = runner.invoke(query_cep, ["--database-url", db_url, cep])
    assert result.exit_code == 3
    assert result.stderr.strip() == "CEP not found"
    mocked_cep_querier.return_value.query.assert_called_once_with(cep)


def test_cli_query_cep_uses_default_table_name(mocked_cep_querier):
    runner = CliRunner()
    runner.invoke(query_cep, ["-db", "db-url", "12345678"])

    mocked_cep_querier.assert_called_once_with("db-url", cep_table_name=None)


def test_cli_query_cep_with_custom_table_name(mocked_cep_querier):
    mocked_cep_querier.return_value.query.return_value = {"cep": "12345678"}

    runner = CliRunner()
    result = runner.invoke(
        query_cep,
        ["-db", "db-url", "--cep-table-name", "my_cep", "12345678"],
    )

    assert result.exit_code == 0
    mocked_cep_querier.assert_called_once_with("db-url", cep_table_name="my_cep")


def test_cli_query_cep_capture_and_display_errors(mocked_cep_querier):
    db_url = "db-url-here"
    cep = "01319-010"
    mocked_cep_querier.return_value.query.side_effect = Exception("some nasty error")

    runner = CliRunner()
    result = runner.invoke(query_cep, ["--database-url", db_url, cep])

    assert result.exit_code == 1
    assert result.stderr.strip() == "ERROR: some nasty error"
    mocked_cep_querier.return_value.query.assert_called_once_with(cep)


@pytest.fixture
def mocked_clickhouse_writer(mocker):
    return mocker.patch("edne_correios_loader.cli.ClickHouseWriter")


@pytest.fixture
def mocked_dne_resolver(mocker):
    return mocker.patch("edne_correios_loader.cli.DneResolver")


def test_cli_sync_clickhouse_command_uses_default_options(
    mocked_clickhouse_writer, mocked_dne_resolver
):
    runner = CliRunner()
    result = runner.invoke(sync_clickhouse, [])

    mocked_clickhouse_writer.assert_called_once()
    call_kwargs = mocked_clickhouse_writer.call_args[1]

    assert call_kwargs["host"] == "localhost"
    assert call_kwargs["port"] == 9000
    assert call_kwargs["database"] == "default"
    assert call_kwargs["user"] == "default"
    assert call_kwargs["password"] == ""

    assert result.exit_code == 0


def test_cli_sync_clickhouse_command_accepts_custom_options(
    mocked_clickhouse_writer, mocked_dne_resolver
):
    runner = CliRunner()
    result = runner.invoke(
        sync_clickhouse,
        [
            "-ch",
            "clickhouse.example.com",
            "-cp",
            "9001",
            "-cdb",
            "analytics",
            "-cu",
            "admin",
            "-cpw",
            "secret123",
        ],
    )

    mocked_clickhouse_writer.assert_called_once()
    call_kwargs = mocked_clickhouse_writer.call_args[1]

    assert call_kwargs["host"] == "clickhouse.example.com"
    assert call_kwargs["port"] == 9001
    assert call_kwargs["database"] == "analytics"
    assert call_kwargs["user"] == "admin"
    assert call_kwargs["password"] == "secret123"

    assert result.exit_code == 0


def test_cli_sync_clickhouse_command_show_error_when_failed(
    mocked_clickhouse_writer, mocked_dne_resolver
):
    exc = Exception("Conexão recusada com ClickHouse")
    mocked_clickhouse_writer.return_value.__enter__.side_effect = exc

    runner = CliRunner()
    result = runner.invoke(sync_clickhouse, [])

    assert result.exit_code == 1
    assert "Conexão recusada com ClickHouse" in result.stderr
