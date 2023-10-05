import pytest
import sqlalchemy as sa

from dne_correios_loader import CepQuerier
from dne_correios_loader.tables import metadata

cep1 = {
    "cep": "11111111",
    "logradouro": None,
    "complemento": None,
    "bairro": "Distrito do Ipiranga do Bom Jesus",
    "municipio": "Ipiranga do Bom Jesus",
    "municipio_cod_ibge": 334455,
    "uf": "SP",
    "nome": None,
}

cep2 = {
    "cep": "55555551",
    "logradouro": "Rua Comendador Inácio",
    "complemento": "502",
    "bairro": "Bairro de Ipiranga do Bom Jesus",
    "municipio": "Ipiranga do Bom Jesus",
    "municipio_cod_ibge": 334455,
    "uf": "SP",
    "nome": "Condomínio Alto",
}


@pytest.fixture(autouse=True)
def populate_ceps_table(connection_url):
    cep_unificado = metadata.tables["cep_unificado"]

    with sa.create_engine(connection_url).connect() as connection:
        metadata.create_all(connection, tables=[cep_unificado])

        connection.execute(
            cep_unificado.insert(),
            [cep1, cep2],
        )

        connection.commit()


def test_cep_querier_returns_cep_when_it_exists(connection_url):
    assert CepQuerier(connection_url).query(cep1["cep"]) == cep1
    assert CepQuerier(connection_url).query(cep2["cep"]) == cep2


def test_cep_querier_normalizes_the_cep_value(connection_url):
    assert CepQuerier(connection_url).query("11111-111") == cep1
    assert CepQuerier(connection_url).query("55555-551") == cep2


def test_cep_querier_returns_none_when_cep_does_not_exist(connection_url):
    assert CepQuerier(connection_url).query("33333333") is None
