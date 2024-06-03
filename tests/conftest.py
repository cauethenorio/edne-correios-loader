import contextlib
import os
import tempfile
from http.client import HTTPResponse

import pytest
import sqlalchemy as sa
from dotenv import load_dotenv
from testcontainers.mysql import MySqlContainer
from testcontainers.postgres import PostgresContainer

from .dne_data import (
    create_sorted_rows,
    generate_bairro,
    generate_localidade,
    generate_logradouro,
)
from .shared import CreateTemporaryDneDirectory

load_dotenv()

### dbs


def get_external_connection_url(prefix, user, password, db, port, host):
    """
    Build a connection url from environment variables if they are defined.
    If true, probably there are docker containers running the databases.
    """
    try:
        return f"{prefix}://{os.environ[user]}:{os.environ[password]}@{os.environ[host]}:{os.environ[port]}/{os.environ[db]}"
    except KeyError:
        return None


@pytest.fixture(scope="session")
def postgres_connection_url():
    if external_connection_url := get_external_connection_url(
        "postgresql",
        user="POSTGRES_USER",
        password="POSTGRES_PASSWORD",
        db="POSTGRES_DB",
        port="POSTGRES_PORT",
        host="POSTGRES_HOST",
    ):
        yield external_connection_url
    else:
        with PostgresContainer("postgres:16.0").with_command(
            "postgres -c fsync=off"
        ) as postgres:
            yield postgres.get_connection_url()


@pytest.fixture(scope="session")
def mysql_connection_url():
    if external_connection_url := get_external_connection_url(
        "mysql+pymysql",
        user="MYSQL_USER",
        password="MYSQL_PASSWORD",
        db="MYSQL_DATABASE",
        port="MYSQL_PORT",
        host="MYSQL_HOST",
    ):
        yield external_connection_url
    else:
        with MySqlContainer("mysql:8.4") as mysql:
            yield mysql.get_connection_url()


@pytest.fixture(scope="session")
def sqlite_temp_db_path():
    with tempfile.TemporaryDirectory() as directory:
        yield directory


@pytest.fixture(params=["postgres", "mysql", "sqlite"])
def connection_url(
    request, postgres_connection_url, mysql_connection_url, sqlite_temp_db_path
):
    if request.param == "postgres":
        connection_url = postgres_connection_url
    elif request.param == "mysql":
        connection_url = mysql_connection_url
    else:
        connection_url = f"sqlite:///{sqlite_temp_db_path}/dne-test.db"

    yield connection_url

    engine = sa.create_engine(connection_url)
    metadata = sa.MetaData()
    metadata.reflect(bind=engine)
    metadata.drop_all(engine, checkfirst=True)


@pytest.fixture(scope="session", autouse=True)
def faker_session_locale():
    return ["pt_BR"]


@pytest.fixture
def generate_localidades(faker):
    def generate_localidades_fn(nrows):
        return create_sorted_rows(lambda: generate_localidade(faker), nrows)

    return generate_localidades_fn


@pytest.fixture
def generate_bairros(faker, generate_localidades):
    def generate_bairros_fn(nrows, localidades=None):
        localidades = localidades or generate_localidades(nrows)
        return create_sorted_rows(lambda: generate_bairro(faker, localidades), nrows)

    return generate_bairros_fn


@pytest.fixture
def generate_logradouros(faker, generate_localidades, generate_bairros):
    def generate_logradouros_fn(nrows, localidades=None, bairros=None):
        localidades = localidades or generate_localidades(nrows)
        bairros = bairros or generate_bairros(nrows, localidades)

        return create_sorted_rows(
            lambda: generate_logradouro(faker, localidades, bairros), nrows
        )

    return generate_logradouros_fn


@pytest.fixture
def stringify_row():
    def stringify_row_fn(row):
        return [str(f) if f else None for f in row]

    return stringify_row_fn


### requests related


@pytest.fixture
def mock_urlopen(mocker):
    some_valid_url = "https://some-valid-url"
    urlopen = mocker.patch("edne_correios_loader.resolver.urllib.request.urlopen")

    @contextlib.contextmanager
    def mock_urlopen_fn(content, *, url=some_valid_url, with_content_length=True):
        if isinstance(content, Exception):
            urlopen.side_effect = content
        else:
            response = mocker.Mock(autospec=HTTPResponse)
            response.headers = {}
            if with_content_length:
                response.headers["Content-Length"] = len(content)

            response.read.side_effect = [content, None]
            urlopen.return_value.__enter__.return_value = response

        yield url

        urlopen.assert_called_once_with(url)
        urlopen.reset_mock()

    return mock_urlopen_fn


### file-reader related


@pytest.fixture
def temporary_dne_dir():
    with CreateTemporaryDneDirectory() as dne_dir:
        yield dne_dir
