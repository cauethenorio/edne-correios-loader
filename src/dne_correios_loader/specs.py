from dataclasses import dataclass
from typing import Optional


@dataclass
class LoadableDneTable:
    """
    Represents a table to be populated from one or multiple DNE files.
    """

    def __init__(
        self,
        table_name: str,
        *,
        file_glob: Optional[str] = None,
        required_for_cep_search: bool = False,
    ):
        self.table_name = table_name

        if file_glob is None:
            file_glob = f"{table_name.upper()}.TXT"

        self.file_glob = file_glob
        self.required_for_cep_search = required_for_cep_search


"""
Specifies the tables to be populated and the source files to be used.
"""
loadable_tables = [
    LoadableDneTable("log_faixa_uf"),
    LoadableDneTable("log_localidade", required_for_cep_search=True),
    LoadableDneTable("ect_pais"),
    LoadableDneTable("log_var_loc"),
    LoadableDneTable("log_faixa_localidade"),
    LoadableDneTable("log_bairro", required_for_cep_search=True),
    LoadableDneTable("log_cpc", required_for_cep_search=True),
    LoadableDneTable("log_var_bai"),
    LoadableDneTable("log_faixa_bairro"),
    LoadableDneTable("log_faixa_cpc"),
    LoadableDneTable(
        "log_logradouro",
        file_glob="LOG_LOGRADOURO_*.TXT",
        required_for_cep_search=True,
    ),
    LoadableDneTable("log_var_log"),
    LoadableDneTable("log_num_sec"),
    LoadableDneTable("log_grande_usuario", required_for_cep_search=True),
    LoadableDneTable("log_unid_oper", required_for_cep_search=True),
    LoadableDneTable("log_faixa_uop"),
    LoadableDneTable("cep_unificado", required_for_cep_search=True, file_glob=""),
]
