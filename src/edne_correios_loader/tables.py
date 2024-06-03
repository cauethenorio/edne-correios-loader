import enum

from sqlalchemy import (
    Column,
    Enum,
    ForeignKey,
    Integer,
    MetaData,
    String,
    Table,
)

metadata = MetaData()


"""
Faixa de CEP de UF
"""
log_faixa_uf = Table(
    "log_faixa_uf",
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
)


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


"""
Localidade

O arquivo LOG_LOCALIDADE contempla os municípios, distritos e povoados do Brasil.

Os CEPs presentes neste arquivo valem para todos os logradouros da cidade, não
necessitando consulta nos demais arquivos.

As localidades em fase de codificação(LOC_IN_SIT=3) estão em período de transição,
sendo aceito o CEP Geral ou os CEPs de Logradouros para endereçamento.
"""
log_localidade = Table(
    "log_localidade",
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
    # CEP da localidade(para localidade não codificada, ou seja, loc_in_sit = 0)
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
        Enum(TipoLocalidadeEnum, values_callable=lambda x: [e.value for e in x]),
        comment="Tipo de localidade",
        nullable=False,
    ),
    Column(
        "loc_nu_sub",
        ForeignKey("log_localidade.loc_nu", ondelete="NO ACTION"),
        index=True,
        comment="Chave da localidade de subordinação",
    ),
    Column("loc_no_abrev", String(36), comment="Abreviatura do nome da localidade"),
    Column("mun_nu", Integer, comment="Código do município IBGE"),
)


"""
Outras denominações da Localidade (denominação popular, denominação anterior)
"""
log_var_loc = Table(
    "log_var_loc",
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
)


class TipoFaixaCepEnum(enum.Enum):
    """
    Tipo de faixa de CEP

    T - Total do município
    C - Exclusiva da sede urbana
    """

    TOTAL_MUNICIPIO = "T"
    EXCLUSIVA_SEDE_URBANA = "C"


"""
Faixa de CEP das Localidades codificadas

Este arquivo contém dados relativos às faixas de CEP das localidades classificadas na
categoria político-administrativa de município codificadas com CEP único ou codificadas
por logradouros.
"""
log_faixa_localidade = Table(
    "log_faixa_localidade",
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
        Enum(TipoFaixaCepEnum, values_callable=lambda x: [e.value for e in x]),
        primary_key=True,
        comment="Tipo de faixa de CEP",
    ),
)

"""
Bairro
"""
log_bairro = Table(
    "log_bairro",
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
)

"""
Outras denominações do Bairro Localidade (denominação popular, denominação anterior)
"""
log_var_bai = Table(
    "log_var_bai",
    metadata,
    Column(
        "bai_nu",
        ForeignKey(log_bairro.c.bai_nu),
        primary_key=True,
        comment="Chave do bairro",
    ),
    Column("vdb_nu", Integer, primary_key=True, comment="Ordem da denominação"),
    Column("vdb_tx", String(72), comment="Denominação", nullable=False),
)


"""
Faixa de CEP de Bairro
"""
log_faixa_bairro = Table(
    "log_faixa_bairro",
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
    Column("fcb_cep_fim", String(8), comment="CEP final do bairro", nullable=False),
)


"""
Caixa Postal Comunitária (CPC)

São áreas rurais e/ou urbanas periféricas não atendidas pela distribuição domiciliária.
"""
log_cpc = Table(
    "log_cpc",
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
    Column("cpc_endereco", String(100), comment="Endereço da CPC", nullable=False),
    Column("cep", String(8), index=True, comment="CEP da CPC", nullable=False),
)

"""
Faixa de Caixa Postal Comunitária
"""
log_faixa_cpc = Table(
    "log_faixa_cpc",
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
)


"""
Logradouro

Este arquivo contém os registros das localidades codificadas por logradouro
(LOC_IN_SIT=1) e de localidades em fase de codificação (LOC_IN_SIT=3).

Para encontrar o bairro do logradouro, utilize o campo BAI_NU_INI
(relacionamento com LOG_BAIRRO, campo BAI_NU)
"""
log_logradouro = Table(
    "log_logradouro",
    metadata,
    Column("log_nu", Integer, primary_key=True, comment="Chave do logradouro"),
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
    Column("log_no", String(100), comment="Nome do logradouro", nullable=False),
    Column("log_complemento", String(100), comment="Complemento"),
    Column(
        "cep",
        String(8),
        index=True,
        comment="CEP do logradouro",
        nullable=False,
    ),
    Column("tlo_tx", String(36), comment="Tipo de logradouro", nullable=False),
    Column(
        "log_sta_tlo",
        String(1),
        index=True,
        comment="Indicador de utilização do tipo de logradouro (S/N)",
    ),
    Column("log_no_abrev", String(36), comment="Abreviatura do nome do logradouro"),
    info={"file_glob": "LOG_LOGRADOURO_*.TXT"},
)


"""
Outras denominações do Logradouro (denominação popular, denominação anterior)
"""
log_var_log = Table(
    "log_var_log",
    metadata,
    Column(
        "log_nu",
        ForeignKey(log_logradouro.c.log_nu),
        primary_key=True,
        comment="Chave do logradouro",
    ),
    Column("vlo_nu", Integer, primary_key=True, comment="Ordem da denominação"),
    Column("tlo_tx", String(36), comment="Tipo de logradouro da variação"),
    Column("vlo_tx", String(150), comment="Nome da variação do logradouro"),
)


class SeccionamentoLadoEnum(enum.Enum):
    """
    Indica a paridade/lado do seccionamento
    """

    AMBOS = "A"
    PAR = "P"
    IMPAR = "I"
    DIREITO = "D"
    ESQUERDO = "E"


"""
Faixa numérica do seccionamento
"""
log_num_sec = Table(
    "log_num_sec",
    metadata,
    Column(
        "log_nu",
        ForeignKey(log_logradouro.c.log_nu),
        primary_key=True,
        comment="Chave do logradouro",
    ),
    Column("sec_nu_ini", String(10), comment="Número inicial do seccionamento"),
    Column("sec_nu_fim", String(10), comment="Número final do seccionamento"),
    Column(
        "sec_in_lado",
        Enum(
            SeccionamentoLadoEnum,
            values_callable=lambda x: [e.value for e in x],
        ),
        comment="Indica a paridade/lado do seccionamento",
    ),
)


"""
Grande usuário

São clientes com grande volume postal (empresas, universidades, bancos,
órgãos públicos, etc).

O campo LOG_NU está sem conteúdo para as localidades não codificadas(LOC_IN_SIT=0),
devendo ser utilizado o campo GRU_ENDEREÇO para  endereçamento.
"""
log_grande_usuario = Table(
    "log_grande_usuario",
    metadata,
    Column("gru_nu", Integer, primary_key=True, comment="Chave do grande usuário"),
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
    Column("gru_no", String(72), comment="Nome do grande usuário", nullable=False),
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
)

"""
Unidade Operacional dos Correios.

São agências próprias ou terceirizadas, centros de distribuição, etc.
O campo LOG_NU está sem conteúdo para as localidades não codificadas(LOC_IN_SIT=0),
devendo ser utilizado o campo UOP_ENDEREÇO para endereçamento.
"""
log_unid_oper = Table(
    "log_unid_oper",
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
)


"""
Faixa de Caixa Postal - UOP
"""
log_faixa_uop = Table(
    "log_faixa_uop",
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
)


"""
Relação dos Nomes dos Países, suas siglas e grafias em inglês e francês
"""
ect_pais = Table(
    "ect_pais",
    metadata,
    Column("pai_sg", String(2), primary_key=True, comment="Sigla do país"),
    Column("pai_sg_alternativa", String(3), comment="Sigla alternativa do país"),
    Column("pai_no_portugues", String(72), comment="Nome do país em português"),
    Column("pai_no_ingles", String(72), comment="Nome do país em inglês"),
    Column("pai_no_frances", String(72), comment="Nome do país em francês"),
    Column("pai_abreviatura", String(36), comment="Abreviatura do nome do país"),
)


"""
Tabela unificada de CEP

Não inclusa no DNE, é populada com dados das outras tabelas depois que a importação
é concluída.
"""
cep_unificado = Table(
    "cep_unificado",
    metadata,
    Column("cep", String(8), primary_key=True),
    Column("logradouro", String(100)),
    Column("complemento", String(100)),
    Column("bairro", String(72)),
    Column("municipio", String(72), nullable=False),
    Column("municipio_cod_ibge", Integer, nullable=False),
    Column("uf", String(2), nullable=False),
    # In some special cases, a CEP is assigned to a single address and may have a name.
    # That happens for government agencies, large clients, some condos,
    # Correios' own buildings, etc.
    Column("nome", String(100)),
    info={"unified_table": True},
)
