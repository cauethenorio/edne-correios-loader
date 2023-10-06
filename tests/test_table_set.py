import pytest

from edne_correios_loader.table_set import (
    TableSetEnum,
    get_cep_tables,
    get_table_files_glob,
)


def test_get_cep_tables():
    assert get_cep_tables() == [
        "cep_unificado",
        "log_localidade",
        "log_bairro",
        "log_cpc",
        "log_logradouro",
        "log_grande_usuario",
        "log_unid_oper",
    ]


def test_get_tables_files_glob():
    assert get_table_files_glob("log_faixa_uf") == "LOG_FAIXA_UF.TXT"
    assert get_table_files_glob("log_logradouro") == "LOG_LOGRADOURO_*.TXT"
    assert get_table_files_glob("cep_unificado") is None


@pytest.mark.parametrize(
    "table_set,tables_to_populate",
    [
        (
            TableSetEnum.ALL_TABLES,
            [
                "cep_unificado",
                "ect_pais",
                "log_faixa_uf",
                "log_localidade",
                "log_bairro",
                "log_cpc",
                "log_faixa_localidade",
                "log_var_loc",
                "log_faixa_bairro",
                "log_faixa_cpc",
                "log_logradouro",
                "log_var_bai",
                "log_grande_usuario",
                "log_num_sec",
                "log_unid_oper",
                "log_var_log",
                "log_faixa_uop",
            ],
        ),
        (
            TableSetEnum.CEP_TABLES,
            [
                "cep_unificado",
                "log_localidade",
                "log_bairro",
                "log_cpc",
                "log_logradouro",
                "log_grande_usuario",
                "log_unid_oper",
            ],
        ),
        (
            TableSetEnum.UNIFIED_CEP_ONLY,
            [
                "cep_unificado",
                "log_localidade",
                "log_bairro",
                "log_cpc",
                "log_logradouro",
                "log_grande_usuario",
                "log_unid_oper",
            ],
        ),
    ],
)
def test_table_set_to_populate(table_set, tables_to_populate):
    assert table_set.to_populate == tables_to_populate


@pytest.mark.parametrize(
    "table_set,tables_to_drop",
    [
        (TableSetEnum.ALL_TABLES, []),
        (TableSetEnum.CEP_TABLES, []),
        (
            TableSetEnum.UNIFIED_CEP_ONLY,
            [
                "ect_pais",
                "log_faixa_uf",
                "log_localidade",
                "log_bairro",
                "log_cpc",
                "log_faixa_localidade",
                "log_var_loc",
                "log_faixa_bairro",
                "log_faixa_cpc",
                "log_logradouro",
                "log_var_bai",
                "log_grande_usuario",
                "log_num_sec",
                "log_unid_oper",
                "log_var_log",
                "log_faixa_uop",
            ],
        ),
    ],
)
def test_table_set_to_drop(table_set, tables_to_drop):
    assert table_set.to_drop == tables_to_drop
