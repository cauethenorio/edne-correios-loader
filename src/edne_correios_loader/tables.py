import enum
from collections.abc import Callable

from sqlalchemy import (
    Column,
    Enum,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
)

"""
Type for customizing table names.

Can be a callable that transforms original names, or a dict mapping
original names to custom names (unmapped names keep their defaults).
"""
TableNameResolver = Callable[[str], str] | dict[str, str]

"""
List of all default table names created by build_metadata().
"""
DEFAULT_TABLE_NAMES = [
    "log_faixa_uf",
    "log_localidade",
    "log_var_loc",
    "log_faixa_localidade",
    "log_bairro",
    "log_var_bai",
    "log_faixa_bairro",
    "log_cpc",
    "log_faixa_cpc",
    "log_logradouro",
    "log_var_log",
    "log_num_sec",
    "log_grande_usuario",
    "log_unid_oper",
    "log_faixa_uop",
    "ect_pais",
    "cep_unificado",
]


def make_table_name_fn(resolver: TableNameResolver | None) -> Callable[[str], str]:
    if resolver is None:
        return lambda name: name
    if isinstance(resolver, dict):
        mapping = resolver
        return lambda name: mapping.get(name, name)
    return resolver


class SituacaoLocalidadeEnum(enum.Enum):
    """
    Situação da localidade

    0 - Localidade não codificada ao nível de Logradouro
    1 - Localidade codificada ao nível de Logradouro
    2 - Distrito ou Povoado inserido na codificação ao nível de Logradouro
    3 - Localidade em fase de codificação ao nível de Logradouro
    """

    def __str__(self):
        return self.value

    NAO_CODIFICADA = "0"
    CODIFICADA = "1"
    DISTRITO = "2"
    FASE_CODIFICACAO = "3"


class TipoLocalidadeEnum(enum.Enum):
    """
    Tipo de localidade
    """

    def __str__(self):
        return self.value

    DISTRITO = "D"
    MUNICIPIO = "M"
    POVOADO = "P"


class TipoFaixaCepEnum(enum.Enum):
    """
    Tipo de faixa de CEP

    T - Total do município
    C - Exclusiva da sede urbana
    """

    TOTAL_MUNICIPIO = "T"
    EXCLUSIVA_SEDE_URBANA = "C"


class SeccionamentoLadoEnum(enum.Enum):
    """
    Indica a paridade/lado do seccionamento
    """

    AMBOS = "A"
    PAR = "P"
    IMPAR = "I"
    DIREITO = "D"
    ESQUERDO = "E"


def build_metadata(table_names: TableNameResolver | None = None) -> MetaData:
    """
    Build a SQLAlchemy MetaData with all DNE table definitions.

    Optionally accepts a TableNameResolver to customize table names.
    When not provided, tables use their default names.
    """
    n = make_table_name_fn(table_names)
    metadata = MetaData()

    def info(original_name, **extra):
        return {"original_name": original_name, **extra}

    """
    Faixa de CEP de UF
    """
    Table(
        n("log_faixa_uf"),
        metadata,
        Column(
            "ufe_sg",
            String(2),
            primary_key=True,
            comment="Sigla da UF",
            nullable=False,
        ),
        Column(
            "ufe_cep_ini",
            String(8),
            primary_key=True,
            comment="CEP inicial da UF",
            nullable=False,
        ),
        Column("ufe_cep_fim", String(8), comment="CEP final da UF", nullable=False),
        info=info("log_faixa_uf"),
    )

    """
    Localidade

    O arquivo LOG_LOCALIDADE contempla os municípios, distritos e povoados do Brasil.

    Os CEPs presentes neste arquivo valem para todos os logradouros da cidade, não
    necessitando consulta nos demais arquivos.

    As localidades em fase de codificação(LOC_IN_SIT=3) estão em período de transição,
    sendo aceito o CEP Geral ou os CEPs de Logradouros para endereçamento.
    """
    log_localidade = Table(
        n("log_localidade"),
        metadata,
        Column(
            "loc_nu",
            Integer,
            primary_key=True,
            unique=True,
            comment="Chave da localidade",
            nullable=False,
        ),
        Column(
            "ufe_sg",
            String(2),
            primary_key=True,
            comment="Sigla da UF",
            nullable=False,
        ),
        Column("loc_no", String(72), comment="Nome da localidade", nullable=False),
        Column("cep", String(8), index=True, comment="CEP da localidade"),
        Column(
            "loc_in_sit",
            Enum(
                SituacaoLocalidadeEnum,
                values_callable=lambda x: [e.value for e in x],
            ),
            comment="Situação da localidade",
            nullable=False,
        ),
        Column(
            "loc_in_tipo_loc",
            Enum(
                TipoLocalidadeEnum,
                values_callable=lambda x: [e.value for e in x],
            ),
            comment="Tipo de localidade",
            nullable=False,
        ),
        Column(
            "loc_nu_sub",
            ForeignKey(n("log_localidade") + ".loc_nu", ondelete="NO ACTION"),
            index=True,
            comment="Chave da localidade de subordinação",
        ),
        Column(
            "loc_no_abrev",
            String(36),
            comment="Abreviatura do nome da localidade",
        ),
        Column("mun_nu", Integer, comment="Código do município IBGE"),
        info=info("log_localidade"),
    )

    """
    Outras denominações da Localidade (denominação popular, denominação anterior)
    """
    Table(
        n("log_var_loc"),
        metadata,
        Column(
            "loc_nu",
            ForeignKey(log_localidade.c.loc_nu),
            primary_key=True,
            comment="Chave da localidade",
        ),
        Column(
            "val_nu",
            Integer,
            primary_key=True,
            comment="Ordem da denominação",
        ),
        Column("val_tx", String(72), comment="Denominação", nullable=False),
        info=info("log_var_loc"),
    )

    """
    Faixa de CEP das Localidades codificadas
    """
    Table(
        n("log_faixa_localidade"),
        metadata,
        Column(
            "loc_nu",
            ForeignKey(log_localidade.c.loc_nu),
            primary_key=True,
            comment="Chave da localidade",
        ),
        Column(
            "loc_cep_ini",
            String(8),
            primary_key=True,
            comment="CEP inicial da localidade",
        ),
        Column("loc_cep_fim", String(8), comment="CEP final da localidade"),
        Column(
            "loc_tipo_faixa",
            Enum(
                TipoFaixaCepEnum,
                values_callable=lambda x: [e.value for e in x],
            ),
            primary_key=True,
            comment="Tipo de faixa de CEP",
        ),
        info=info("log_faixa_localidade"),
    )

    """
    Bairro
    """
    log_bairro = Table(
        n("log_bairro"),
        metadata,
        Column("bai_nu", Integer, primary_key=True, comment="Chave do bairro"),
        Column("ufe_sg", String(2), comment="Sigla da UF", nullable=False),
        Column(
            "loc_nu",
            ForeignKey(log_localidade.c.loc_nu),
            index=True,
            comment="Chave da localidade",
            nullable=False,
        ),
        Column("bai_no", String(72), comment="Nome do bairro", nullable=False),
        Column(
            "bai_no_abrev",
            String(36),
            comment="Abreviatura do nome do bairro",
        ),
        info=info("log_bairro"),
    )

    """
    Outras denominações do Bairro
    """
    Table(
        n("log_var_bai"),
        metadata,
        Column(
            "bai_nu",
            ForeignKey(log_bairro.c.bai_nu),
            primary_key=True,
            comment="Chave do bairro",
        ),
        Column(
            "vdb_nu",
            Integer,
            primary_key=True,
            comment="Ordem da denominação",
        ),
        Column("vdb_tx", String(72), comment="Denominação", nullable=False),
        info=info("log_var_bai"),
    )

    """
    Faixa de CEP de Bairro
    """
    Table(
        n("log_faixa_bairro"),
        metadata,
        Column(
            "bai_nu",
            ForeignKey(log_bairro.c.bai_nu),
            primary_key=True,
            comment="Chave do bairro",
        ),
        Column(
            "fcb_cep_ini",
            String(8),
            primary_key=True,
            comment="CEP inicial do bairro",
        ),
        Column(
            "fcb_cep_fim",
            String(8),
            comment="CEP final do bairro",
            nullable=False,
        ),
        info=info("log_faixa_bairro"),
    )

    """
    Caixa Postal Comunitária (CPC)
    """
    log_cpc = Table(
        n("log_cpc"),
        metadata,
        Column(
            "cpc_nu",
            Integer,
            primary_key=True,
            comment="Chave da caixa postal comunitária",
        ),
        Column("ufe_sg", String(2), comment="Sigla da UF", nullable=False),
        Column(
            "loc_nu",
            ForeignKey(log_localidade.c.loc_nu),
            index=True,
            comment="Chave da localidade",
            nullable=False,
        ),
        Column("cpc_no", String(72), comment="Nome da CPC", nullable=False),
        Column(
            "cpc_endereco",
            String(100),
            comment="Endereço da CPC",
            nullable=False,
        ),
        Column(
            "cep",
            String(8),
            index=True,
            comment="CEP da CPC",
            nullable=False,
        ),
        info=info("log_cpc"),
    )

    """
    Faixa de Caixa Postal Comunitária
    """
    Table(
        n("log_faixa_cpc"),
        metadata,
        Column(
            "cpc_nu",
            ForeignKey(log_cpc.c.cpc_nu),
            primary_key=True,
            comment="Chave da caixa postal comunitária",
        ),
        Column(
            "cpc_inicial",
            String(6),
            comment="Número inicial da caixa postal comunitária",
            primary_key=True,
        ),
        Column(
            "cpc_final",
            String(6),
            comment="Número final da caixa postal comunitária",
            primary_key=True,
        ),
        info=info("log_faixa_cpc"),
    )

    """
    Logradouro
    """
    log_logradouro = Table(
        n("log_logradouro"),
        metadata,
        Column(
            "log_nu",
            Integer,
            primary_key=True,
            comment="Chave do logradouro",
        ),
        Column("ufe_sg", String(2), comment="Sigla da UF", nullable=False),
        Column(
            "loc_nu",
            ForeignKey(log_localidade.c.loc_nu),
            index=True,
            comment="Chave da localidade",
            nullable=False,
        ),
        Column(
            "bai_nu_ini",
            ForeignKey(log_bairro.c.bai_nu),
            index=True,
            comment="Chave do bairro inicial do logradouro",
            nullable=False,
        ),
        Column(
            "bai_nu_fim",
            ForeignKey(log_bairro.c.bai_nu),
            index=True,
            comment="Chave do bairro final do logradouro",
            nullable=True,
        ),
        Column(
            "log_no",
            String(100),
            comment="Nome do logradouro",
            nullable=False,
        ),
        Column("log_complemento", String(100), comment="Complemento"),
        Column(
            "cep",
            String(8),
            index=True,
            comment="CEP do logradouro",
            nullable=False,
        ),
        Column(
            "tlo_tx",
            String(36),
            comment="Tipo de logradouro",
            nullable=False,
        ),
        Column(
            "log_sta_tlo",
            String(1),
            index=True,
            comment="Indicador de utilização do tipo de logradouro (S/N)",
        ),
        Column(
            "log_no_abrev",
            String(36),
            comment="Abreviatura do nome do logradouro",
        ),
        info=info("log_logradouro", file_glob="LOG_LOGRADOURO_*.TXT"),
    )

    """
    Outras denominações do Logradouro
    """
    Table(
        n("log_var_log"),
        metadata,
        Column(
            "log_nu",
            ForeignKey(log_logradouro.c.log_nu),
            primary_key=True,
            comment="Chave do logradouro",
        ),
        Column(
            "vlo_nu",
            Integer,
            primary_key=True,
            comment="Ordem da denominação",
        ),
        Column(
            "tlo_tx",
            String(36),
            comment="Tipo de logradouro da variação",
        ),
        Column(
            "vlo_tx",
            String(150),
            comment="Nome da variação do logradouro",
        ),
        info=info("log_var_log"),
    )

    """
    Faixa numérica do seccionamento
    """
    Table(
        n("log_num_sec"),
        metadata,
        Column(
            "log_nu",
            ForeignKey(log_logradouro.c.log_nu),
            primary_key=True,
            comment="Chave do logradouro",
        ),
        Column(
            "sec_nu_ini",
            String(10),
            comment="Número inicial do seccionamento",
        ),
        Column(
            "sec_nu_fim",
            String(10),
            comment="Número final do seccionamento",
        ),
        Column(
            "sec_in_lado",
            Enum(
                SeccionamentoLadoEnum,
                values_callable=lambda x: [e.value for e in x],
            ),
            comment="Indica a paridade/lado do seccionamento",
        ),
        info=info("log_num_sec"),
    )

    """
    Grande usuário
    """
    Table(
        n("log_grande_usuario"),
        metadata,
        Column(
            "gru_nu",
            Integer,
            primary_key=True,
            comment="Chave do grande usuário",
        ),
        Column("ufe_sg", String(2), comment="Sigla da UF", nullable=False),
        Column(
            "loc_nu",
            ForeignKey(log_localidade.c.loc_nu),
            index=True,
            comment="Chave da localidade",
            nullable=False,
        ),
        Column(
            "bai_nu",
            ForeignKey(log_bairro.c.bai_nu),
            index=True,
            comment="Chave do bairro",
            nullable=False,
        ),
        Column(
            "log_nu",
            ForeignKey(log_logradouro.c.log_nu),
            index=True,
            comment="Chave do logradouro",
        ),
        Column(
            "gru_no",
            String(72),
            comment="Nome do grande usuário",
            nullable=False,
        ),
        Column(
            "gru_endereco",
            String(100),
            comment="Endereço do grande usuário",
            nullable=False,
        ),
        Column(
            "cep",
            String(8),
            index=True,
            comment="CEP do grande usuário",
            nullable=False,
        ),
        Column(
            "gru_no_abrev",
            String(36),
            comment="Abreviatura do nome do grande usuário",
        ),
        info=info("log_grande_usuario"),
    )

    """
    Unidade Operacional dos Correios.
    """
    log_unid_oper = Table(
        n("log_unid_oper"),
        metadata,
        Column(
            "uop_nu",
            Integer,
            primary_key=True,
            comment="Chave da unidade operacional",
        ),
        Column("ufe_sg", String(2), comment="Sigla da UF", nullable=False),
        Column(
            "loc_nu",
            ForeignKey(log_localidade.c.loc_nu),
            index=True,
            comment="Chave da localidade",
            nullable=False,
        ),
        Column(
            "bai_nu",
            ForeignKey(log_bairro.c.bai_nu),
            index=True,
            comment="Chave do bairro",
            nullable=False,
        ),
        Column(
            "log_nu",
            ForeignKey(log_logradouro.c.log_nu),
            index=True,
            comment="Chave do logradouro",
        ),
        Column(
            "uop_no",
            String(100),
            comment="Nome da unidade operacional",
            nullable=False,
        ),
        Column(
            "uop_endereco",
            String(100),
            comment="Endereço da unidade operacional",
            nullable=False,
        ),
        Column(
            "cep",
            String(8),
            index=True,
            comment="CEP da unidade operacional",
            nullable=False,
        ),
        Column(
            "uop_in_cp",
            String(1),
            comment="Indicador de unidade operacional com caixa postal (S/N)",
        ),
        Column(
            "uop_no_abrev",
            String(36),
            comment="Abreviatura do nome da unidade operacional",
        ),
        info=info("log_unid_oper"),
    )

    """
    Faixa de Caixa Postal - UOP
    """
    Table(
        n("log_faixa_uop"),
        metadata,
        Column(
            "upo_nu",
            ForeignKey(log_unid_oper.c.uop_nu),
            primary_key=True,
            comment="Chave da unidade operacional",
        ),
        Column(
            "fnc_inicial",
            Integer,
            primary_key=True,
            comment="Número inicial da caixa postal",
        ),
        Column(
            "fnc_final",
            Integer,
            comment="Número final da caixa postal",
            nullable=False,
        ),
        info=info("log_faixa_uop"),
    )

    """
    Relação dos Nomes dos Países
    """
    Table(
        n("ect_pais"),
        metadata,
        Column("pai_sg", String(2), primary_key=True, comment="Sigla do país"),
        Column(
            "pai_sg_alternativa",
            String(3),
            comment="Sigla alternativa do país",
        ),
        Column(
            "pai_no_portugues",
            String(72),
            comment="Nome do país em português",
        ),
        Column("pai_no_ingles", String(72), comment="Nome do país em inglês"),
        Column("pai_no_frances", String(72), comment="Nome do país em francês"),
        Column(
            "pai_abreviatura",
            String(36),
            comment="Abreviatura do nome do país",
        ),
        info=info("ect_pais"),
    )

    """
    Tabela unificada de CEP
    """
    Table(
        n("cep_unificado"),
        metadata,
        Column("cep", String(8), primary_key=True),
        Column("logradouro", String(100)),
        Column("complemento", String(100)),
        Column("bairro", String(72)),
        Column("municipio", String(72), nullable=False),
        Column("municipio_cod_ibge", Integer, nullable=False),
        Column("uf", String(2), nullable=False),
        Column("nome", String(100)),
        info=info("cep_unificado", unified_table=True),
    )

    metadata.info["original_name_map"] = {
        t.info["original_name"]: t.name for t in metadata.sorted_tables
    }

    return metadata


def get_table(metadata: MetaData, original_name: str):
    """
    Look up a table by its original (default) name, even if it was renamed.
    """
    original_name_map = metadata.info.get("original_name_map", {})
    table_name = original_name_map.get(original_name)

    if table_name is None:
        msg = f"Table with original name '{original_name}' not found"
        raise KeyError(msg)

    return metadata.tables[table_name]


# Default metadata for backward compatibility
metadata = build_metadata()
