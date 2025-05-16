import sqlalchemy as sa

from edne_correios_loader.tables import (
    SituacaoLocalidadeEnum,
    TipoLocalidadeEnum,
    metadata,
)
from edne_correios_loader.unified_table import (
    populate_unified_table,
    select_logradouros_ceps,
)


def test_populate_unified_table_populates_correctly(connection_url):
    # a municipality without a CEP (its logradouros have CEPs)
    localidade_sp = {
        "loc_nu": 123,
        "ufe_sg": "SP",
        "loc_no": "Ipiranga do Bom Jesus",
        "cep": None,
        "loc_in_sit": SituacaoLocalidadeEnum.CODIFICADA,
        "loc_in_tipo_loc": TipoLocalidadeEnum.MUNICIPIO,
        "loc_nu_sub": None,
        "loc_no_abrev": "Ipiranga do B. Jesus",
        "mun_nu": 334455,
    }

    # a subordinated district within a municipality
    localidade_distrito_sp = {
        "loc_nu": 124,
        "ufe_sg": "SP",
        "loc_no": "Distrito do Ipiranga do Bom Jesus",
        "cep": "11111111",
        "loc_in_sit": SituacaoLocalidadeEnum.NAO_CODIFICADA,
        "loc_in_tipo_loc": TipoLocalidadeEnum.DISTRITO,
        "loc_nu_sub": localidade_sp["loc_nu"],
        "loc_no_abrev": "D. do Ipiranga do B. Jesus",
        "mun_nu": None,
    }

    # a municipality with a CEP
    localidade_ba = {
        "loc_nu": 125,
        "ufe_sg": "BA",
        "loc_no": "Sertãozinho do Bom Jesus",
        "cep": "11111112",
        "loc_in_sit": SituacaoLocalidadeEnum.NAO_CODIFICADA,
        "loc_in_tipo_loc": TipoLocalidadeEnum.MUNICIPIO,
        "loc_nu_sub": None,
        "loc_no_abrev": "S. do B. Jesus",
        "mun_nu": 445566,
    }

    # a municipality with a CEP and without mun_nu
    localidade_sem_cod_ibge = {
        "loc_nu": 126,
        "ufe_sg": "MT",
        "loc_no": "Boa Esperança do None",
        "cep": "11111113",
        "loc_in_sit": SituacaoLocalidadeEnum.NAO_CODIFICADA,
        "loc_in_tipo_loc": TipoLocalidadeEnum.MUNICIPIO,
        "loc_nu_sub": None,
        "loc_no_abrev": "B. E. do None",
        "mun_nu": None,
    }

    # subordinated district within a municipality with no mun_nu
    localidade_distrito_sem_cod_ibge = {
        "loc_nu": 127,
        "ufe_sg": "MT",
        "loc_no": "Distrito de Boa Esperança do None",
        "cep": "11111114",
        "loc_in_sit": SituacaoLocalidadeEnum.NAO_CODIFICADA,
        "loc_in_tipo_loc": TipoLocalidadeEnum.DISTRITO,
        "loc_nu_sub": localidade_sem_cod_ibge["loc_nu"],
        "loc_no_abrev": "D. de B. E. do None",
        "mun_nu": None,
    }

    localidades = [
        localidade_sp,
        localidade_distrito_sp,
        localidade_ba,
        localidade_sem_cod_ibge,
        localidade_distrito_sem_cod_ibge,
    ]

    bairro_sp = {
        "bai_nu": 221,
        "ufe_sg": localidade_sp["ufe_sg"],
        "loc_nu": localidade_sp["loc_nu"],
        "bai_no": "Bairro de Ipiranga do Bom Jesus",
        "bai_no_abrev": "B. de I. do B. Jesus",
    }

    bairro_ba = {
        "bai_nu": 223,
        "ufe_sg": localidade_ba["ufe_sg"],
        "loc_nu": localidade_ba["loc_nu"],
        "bai_no": "Bairro de Sertãozinho do Bom Jesus",
        "bai_no_abrev": "B. de S. do B. Jesus",
    }

    bairros = [bairro_sp, bairro_ba]

    logradouro_sp = {
        "log_nu": 331,
        "ufe_sg": localidade_sp["ufe_sg"],
        "loc_nu": localidade_sp["loc_nu"],
        "bai_nu_ini": bairro_sp["bai_nu"],
        "log_no": "Nome",
        "log_complemento": "Lado ímpar",
        "cep": "33333331",
        "tlo_tx": "Rua",
        "log_sta_tlo": "S",
        "log_no_abrev": None,
    }

    logradouro_ba = {
        "log_nu": 332,
        "ufe_sg": localidade_ba["ufe_sg"],
        "loc_nu": localidade_ba["loc_nu"],
        "bai_nu_ini": bairro_ba["bai_nu"],
        "log_no": "QNG Área Especial 38",
        "log_complemento": None,
        "cep": "33333332",
        "tlo_tx": "Área",
        "log_sta_tlo": "N",
        "log_no_abrev": "QNG A Especial 38",
    }

    logradouros = [logradouro_sp, logradouro_ba]

    cpc_sp = {
        "cpc_nu": 441,
        "ufe_sg": localidade_distrito_sp["ufe_sg"],
        "loc_nu": localidade_distrito_sp["loc_nu"],
        "cpc_no": "Associação dos Moradores",
        "cpc_endereco": "Estrada São Domingos, s/n, Sitio Arraia",
        "cep": "44444441",
    }

    cpc2_sp = {
        "cpc_nu": 442,
        "ufe_sg": localidade_sp["ufe_sg"],
        "loc_nu": localidade_sp["loc_nu"],
        "cpc_no": "CPC Rio Limpo",
        "cpc_endereco": "Rua Gilmar Furtado de Oliveira, 111 - Boiçucanga",
        "cep": "44444442",
    }

    cpc_ba = {
        "cpc_nu": 443,
        "ufe_sg": localidade_ba["ufe_sg"],
        "loc_nu": localidade_ba["loc_nu"],
        "cpc_no": "Velho Horizonte",
        "cpc_endereco": "Rua Secundária",
        "cep": "44444443",
    }

    cpcs = [cpc_sp, cpc2_sp, cpc_ba]

    grande_usuario_sp = {
        "gru_nu": 551,
        "ufe_sg": localidade_distrito_sp["ufe_sg"],
        "loc_nu": localidade_distrito_sp["loc_nu"],
        "bai_nu": bairro_sp["bai_nu"],
        "log_nu": logradouro_sp["log_nu"],
        "gru_no": "Condomínio Alto",
        "gru_endereco": "Rua Comendador Inácio, 502",
        "cep": "55555551",
        "gru_no_abrev": None,
    }

    grande_usuario_ba = {
        "gru_nu": 552,
        "ufe_sg": localidade_ba["ufe_sg"],
        "loc_nu": localidade_ba["loc_nu"],
        "bai_nu": bairro_ba["bai_nu"],
        "log_nu": logradouro_ba["log_nu"],
        "gru_no": "Fundação Getúlio Aurélio",
        "gru_endereco": "SHN Quadra 4 Bloco C",
        "cep": "55555552",
        "gru_no_abrev": "F.G.A.",
    }

    grandes_usuarios = [grande_usuario_sp, grande_usuario_ba]

    uop_sp = {
        "uop_nu": 661,
        "ufe_sg": localidade_distrito_sp["ufe_sg"],
        "loc_nu": localidade_distrito_sp["loc_nu"],
        "bai_nu": bairro_sp["bai_nu"],
        "log_nu": logradouro_sp["log_nu"],
        "uop_no": "AC Ipiranga do Bom Jesus",
        "uop_endereco": "Rua Eurico Gaspar Dutra, 78",
        "cep": "66666661",
        "uop_in_cp": "S",
        "uop_no_abrev": "AC Ipiranga do B. Jesus",
    }

    uop_ba = {
        "uop_nu": 662,
        "ufe_sg": localidade_ba["ufe_sg"],
        "loc_nu": localidade_ba["loc_nu"],
        "bai_nu": bairro_ba["bai_nu"],
        "log_nu": logradouro_ba["log_nu"],
        "uop_no": "CDD Sertãozinho",
        "uop_endereco": "Rua Feia",
        "cep": "66666662",
        "uop_in_cp": "N",
        "uop_no_abrev": "CDD S.",
    }

    # unidade operacional in a municipality with no mun_nu
    uop_sem_cod_ibge = {
        "uop_nu": 663,
        "ufe_sg": localidade_sem_cod_ibge["ufe_sg"],
        "loc_nu": localidade_sem_cod_ibge["loc_nu"],
        "bai_nu": bairro_ba["bai_nu"],
        "log_nu": logradouro_ba["log_nu"],
        "uop_no": "AC Boa Esperança do None",
        "uop_endereco": "Rua Esperança, 78",
        "cep": "66666663",
        "uop_in_cp": "S",
        "uop_no_abrev": "AC B. E. do None",
    }

    unidades_operacionais = [uop_sp, uop_ba, uop_sem_cod_ibge]

    with sa.create_engine(connection_url).connect() as connection:
        metadata.create_all(connection)

        for table_name, rows in (
            ("log_localidade", localidades),
            ("log_bairro", bairros),
            ("log_logradouro", logradouros),
            ("log_cpc", cpcs),
            ("log_grande_usuario", grandes_usuarios),
            ("log_unid_oper", unidades_operacionais),
        ):
            table = metadata.tables[table_name]
            connection.execute(table.insert(), rows)

        populate_unified_table(connection, insert_batch_size=2)

        unified_table = metadata.tables["cep_unificado"]
        pks = [c.name for c in unified_table.primary_key]
        rows = connection.execute(unified_table.select().order_by(*pks)).fetchall()

        rows = [r._mapping for r in rows]

        assert rows == [
            {
                "cep": localidade_distrito_sp["cep"],
                "logradouro": None,
                "complemento": None,
                "bairro": localidade_distrito_sp["loc_no"],
                "municipio": localidade_sp["loc_no"],
                "municipio_cod_ibge": localidade_sp["mun_nu"],
                "uf": localidade_distrito_sp["ufe_sg"],
                "nome": None,
            },
            {
                "cep": localidade_ba["cep"],
                "logradouro": None,
                "complemento": None,
                "bairro": None,
                "municipio": localidade_ba["loc_no"],
                "municipio_cod_ibge": localidade_ba["mun_nu"],
                "uf": localidade_ba["ufe_sg"],
                "nome": None,
            },
            {
                "cep": logradouro_sp["cep"],
                "logradouro": logradouro_sp["tlo_tx"] + " " + logradouro_sp["log_no"],
                "complemento": None,
                "bairro": bairro_sp["bai_no"],
                "municipio": localidade_sp["loc_no"],
                "municipio_cod_ibge": localidade_sp["mun_nu"],
                "uf": logradouro_sp["ufe_sg"],
                "nome": None,
            },
            {
                "cep": logradouro_ba["cep"],
                "logradouro": logradouro_ba["log_no"],
                "complemento": None,
                "bairro": bairro_ba["bai_no"],
                "municipio": localidade_ba["loc_no"],
                "municipio_cod_ibge": localidade_ba["mun_nu"],
                "uf": logradouro_ba["ufe_sg"],
                "nome": None,
            },
            {
                "cep": cpc_sp["cep"],
                "logradouro": cpc_sp["cpc_endereco"].split(",", 1)[0].strip(),
                "complemento": cpc_sp["cpc_endereco"].split(",", 1)[1].strip(),
                "bairro": None,
                "municipio": localidade_sp["loc_no"],
                "municipio_cod_ibge": localidade_sp["mun_nu"],
                "uf": localidade_distrito_sp["ufe_sg"],
                "nome": cpc_sp["cpc_no"],
            },
            {
                "cep": cpc2_sp["cep"],
                "logradouro": cpc2_sp["cpc_endereco"].split(",", 1)[0].strip(),
                "complemento": cpc2_sp["cpc_endereco"].split(",", 1)[1].strip(),
                "bairro": None,
                "municipio": localidade_sp["loc_no"],
                "municipio_cod_ibge": localidade_sp["mun_nu"],
                "uf": localidade_sp["ufe_sg"],
                "nome": cpc2_sp["cpc_no"],
            },
            {
                "cep": cpc_ba["cep"],
                "logradouro": cpc_ba["cpc_endereco"],
                "complemento": None,
                "bairro": None,
                "municipio": localidade_ba["loc_no"],
                "municipio_cod_ibge": localidade_ba["mun_nu"],
                "uf": localidade_ba["ufe_sg"],
                "nome": cpc_ba["cpc_no"],
            },
            {
                "cep": grande_usuario_sp["cep"],
                "logradouro": grande_usuario_sp["gru_endereco"]
                .split(",", 1)[0]
                .strip(),
                "complemento": grande_usuario_sp["gru_endereco"]
                .split(",", 1)[1]
                .strip(),
                "bairro": bairro_sp["bai_no"],
                "municipio": localidade_sp["loc_no"],
                "municipio_cod_ibge": localidade_sp["mun_nu"],
                "uf": localidade_sp["ufe_sg"],
                "nome": grande_usuario_sp["gru_no"],
            },
            {
                "cep": grande_usuario_ba["cep"],
                "logradouro": grande_usuario_ba["gru_endereco"],
                "complemento": None,
                "bairro": bairro_ba["bai_no"],
                "municipio": localidade_ba["loc_no"],
                "municipio_cod_ibge": localidade_ba["mun_nu"],
                "uf": localidade_ba["ufe_sg"],
                "nome": grande_usuario_ba["gru_no"],
            },
            {
                "cep": uop_sp["cep"],
                "logradouro": uop_sp["uop_endereco"].split(",", 1)[0].strip(),
                "complemento": uop_sp["uop_endereco"].split(",", 1)[1].strip(),
                "bairro": bairro_sp["bai_no"],
                "municipio": localidade_sp["loc_no"],
                "municipio_cod_ibge": localidade_sp["mun_nu"],
                "uf": localidade_sp["ufe_sg"],
                "nome": uop_sp["uop_no"],
            },
            {
                "cep": uop_ba["cep"],
                "logradouro": uop_ba["uop_endereco"],
                "complemento": None,
                "bairro": bairro_ba["bai_no"],
                "municipio": localidade_ba["loc_no"],
                "municipio_cod_ibge": localidade_ba["mun_nu"],
                "uf": localidade_ba["ufe_sg"],
                "nome": uop_ba["uop_no"],
            },
        ]


def test_logradouros_with_null_municipio_cod_ibge_excluded(connection_url):
    """Test that logradouros with null municipality codes are excluded."""
    # Municipality with null mun_nu (IBGE code)
    localidade_null_ibge = {
        "loc_nu": 901,
        "ufe_sg": "MG",
        "loc_no": "Cidade Sem Código IBGE",
        "cep": None,
        "loc_in_sit": SituacaoLocalidadeEnum.CODIFICADA,
        "loc_in_tipo_loc": TipoLocalidadeEnum.MUNICIPIO,
        "loc_nu_sub": None,
        "loc_no_abrev": "C. S. C. IBGE",
        "mun_nu": None,  # Null municipality code
    }

    # Normal municipality with mun_nu
    localidade_with_ibge = {
        "loc_nu": 902,
        "ufe_sg": "MG",
        "loc_no": "Cidade Com Código IBGE",
        "cep": None,
        "loc_in_sit": SituacaoLocalidadeEnum.CODIFICADA,
        "loc_in_tipo_loc": TipoLocalidadeEnum.MUNICIPIO,
        "loc_nu_sub": None,
        "loc_no_abrev": "C. C. C. IBGE",
        "mun_nu": 999999,  # Valid municipality code
    }

    bairro_null_ibge = {
        "bai_nu": 801,
        "ufe_sg": localidade_null_ibge["ufe_sg"],
        "loc_nu": localidade_null_ibge["loc_nu"],
        "bai_no": "Bairro da Cidade Sem Código IBGE",
        "bai_no_abrev": "B. C. S. C. IBGE",
    }

    bairro_with_ibge = {
        "bai_nu": 802,
        "ufe_sg": localidade_with_ibge["ufe_sg"],
        "loc_nu": localidade_with_ibge["loc_nu"],
        "bai_no": "Bairro da Cidade Com Código IBGE",
        "bai_no_abrev": "B. C. C. C. IBGE",
    }

    # Logradouro associated with municipality that has null mun_nu
    logradouro_null_ibge = {
        "log_nu": 701,
        "ufe_sg": localidade_null_ibge["ufe_sg"],
        "loc_nu": localidade_null_ibge["loc_nu"],
        "bai_nu_ini": bairro_null_ibge["bai_nu"],
        "log_no": "Rua da Cidade Sem Código IBGE",
        "log_complemento": None,
        "cep": "77777701",
        "tlo_tx": "Rua",
        "log_sta_tlo": "S",
        "log_no_abrev": None,
    }

    # Logradouro associated with municipality that has valid mun_nu
    logradouro_with_ibge = {
        "log_nu": 702,
        "ufe_sg": localidade_with_ibge["ufe_sg"],
        "loc_nu": localidade_with_ibge["loc_nu"],
        "bai_nu_ini": bairro_with_ibge["bai_nu"],
        "log_no": "Rua da Cidade Com Código IBGE",
        "log_complemento": None,
        "cep": "77777702",
        "tlo_tx": "Rua",
        "log_sta_tlo": "S",
        "log_no_abrev": None,
    }

    with sa.create_engine(connection_url).connect() as connection:
        metadata.create_all(connection)

        # Insert test data
        connection.execute(
            metadata.tables["log_localidade"].insert(),
            [localidade_null_ibge, localidade_with_ibge],
        )
        connection.execute(
            metadata.tables["log_bairro"].insert(),
            [bairro_null_ibge, bairro_with_ibge],
        )
        connection.execute(
            metadata.tables["log_logradouro"].insert(),
            [logradouro_null_ibge, logradouro_with_ibge],
        )

        # Execute the function that should filter out records with null mun_nu
        results = connection.execute(select_logradouros_ceps()).fetchall()

        # Verify that only the logradouro with valid municipality code is included
        ceps = [row.cep for row in results]
        assert logradouro_null_ibge["cep"] not in ceps, (
            "Logradouro with null municipio_cod_ibge should be excluded"
        )
        assert logradouro_with_ibge["cep"] in ceps, (
            "Logradouro with valid municipio_cod_ibge should be included"
        )

        # Verify that the full table population also works
        # Clear the unified table first
        connection.execute(metadata.tables["cep_unificado"].delete())

        # Populate the unified table
        populate_unified_table(connection)

        # Check that only the logradouro with valid municipality code
        # is in the unified table
        unified_results = connection.execute(
            metadata.tables["cep_unificado"].select()
        ).fetchall()
        unified_ceps = [row.cep for row in unified_results]

        assert logradouro_null_ibge["cep"] not in unified_ceps, (
            "Logradouro with null municipio_cod_ibge should not be in unified table"
        )
        assert logradouro_with_ibge["cep"] in unified_ceps, (
            "Logradouro with valid municipio_cod_ibge should be in unified table"
        )
