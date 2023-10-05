import json
from pathlib import Path

import pytest
from click.testing import CliRunner

from dne_correios_loader.cli import (
    DneResolverWithDownloadProgress,
    dne_correios_loader,
    load,
    query_cep,
)
from dne_correios_loader.table_set import TableSetEnum

from .shared import create_inner_dne_zip_file


@pytest.fixture
def mocked_dne_loader(mocker):
    return mocker.patch("dne_correios_loader.cli.DneLoaderWithProgress")


@pytest.fixture
def mocked_cep_querier(mocker):
    return mocker.patch("dne_correios_loader.cli.CepQuerier")


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
    result = runner.invoke(dne_correios_loader)

    assert result.exit_code == 0
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

    mocked_dne_loader.assert_called_once_with(db_url, dne_source=None)
    mocked_dne_loader.return_value.load.assert_called_once_with(
        table_set=TableSetEnum.UNIFIED_CEP_ONLY
    )

    assert result.exit_code == 0


def test_cli_load_command_show_error_stack_when_verbose(mocked_dne_loader):
    db_url = "db-url-here"
    exc = Exception("some nasty error")

    mocked_dne_loader.return_value.load.side_effect = exc

    runner = CliRunner(mix_stderr=False)
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
    mocked_dne_loader.assert_called_once_with(db_url, dne_source=dne_source)
    mocked_dne_loader.return_value.load.assert_called_once_with(table_set=table_set)


def test_cli_query_cep_command_asks_for_required_arguments():
    runner = CliRunner(mix_stderr=False)

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

    runner = CliRunner(mix_stderr=False)
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


def test_cli_query_cep_capture_and_display_errors(mocked_cep_querier):
    db_url = "db-url-here"
    cep = "01319-010"
    mocked_cep_querier.return_value.query.side_effect = Exception("some nasty error")

    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(query_cep, ["--database-url", db_url, cep])

    assert result.exit_code == 1
    assert result.stderr.strip() == "ERROR: some nasty error"
    mocked_cep_querier.return_value.query.assert_called_once_with(cep)
