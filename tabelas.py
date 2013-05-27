# coding: utf-8

import sqlalchemy as sa
from sqlalchemy import orm
from sqlalchemy.ext.declarative import declarative_base

ordem = [
    'LogFaixaUF',
    'LogLocalidade',
    'LogVarLoc',
    'LogFaixaLocalidade',
    'LogBairro',
    'LogVarBai',
    'LogFaixaBairro',
    'LogCpc',
    'LogFaixaCpc',
    'LogLogradouro',
    'LogVarLog',
    'LogNumSec',
    'LogGrandeUsuario',
    'LogUnidOper',
    'LogFaixaUop',
]

Base = declarative_base()


class LogFaixaUF(Base):
    """
        faixa de CEPs de uma UF
    """
    __tablename__ = 'log_faixa_uf'

    # sigla da UF
    ufe_sg = sa.Column(sa.Unicode(2), primary_key=True)

    # CEP inicial da UF
    loc_cep_ini = sa.Column(sa.Unicode(8), primary_key=True, index=True)

    # CEP final da UF
    loc_cep_fim = sa.Column(sa.Unicode(8), index=True)


class LogLocalidade(Base):
    """
        municípios, distritos e povoados do Brasil

        Caso presente, o CEP vale para todos os logradouros da cidade,
        não necessitando consulta nos demais arquivos
    """
    __tablename__ = 'log_localidade'

    # chave da localidade
    loc_nu = sa.Column(sa.Integer, primary_key=True)

    # sigla da UF
    ufe_sg = sa.Column(sa.Unicode(2))

    # nome da localidade
    loc_no = sa.Column(sa.Unicode(72))

    # CEP da localidade não codificada (cidade com um CEP só)
    cep = sa.Column(sa.Unicode(8), index=True, nullable=True)

    # situação da localidade
    #  0 - não codificada em nível de logradouro
    #  1 - codificada em nível de logradouro
    #  2 - distrito ou povoado inserido na codificação em nível de logradouro
    loc_in_sit = sa.Column(sa.Unicode(1))

    # tipo da localidade
    #  D - distrito
    #  M - município
    #  P - povoado
    loc_in_tipo = sa.Column(sa.Unicode(1))

    # chave da localidade de subordinação (localidade mãe)
    loc_nu_sub = sa.Column(sa.Integer,
                           #sa.ForeignKey(loc_nu),
                           nullable=True)

    # abreviatura do nome da localidade
    loc_no_abrev = sa.Column(sa.Unicode(36), nullable=True)

    # código ibge do município
    mun_nu = sa.Column(sa.Unicode(7), nullable=True)


class LogVarLoc(Base):
    """
        outras denominações da localidade
        (denominação popular, denominação anterior)
    """
    __tablename__ = 'log_var_loc'

    # chave da localidade
    loc_nu = sa.Column(sa.Integer,
                       sa.ForeignKey(LogLocalidade.loc_nu, ondelete='CASCADE'),
                       primary_key=True)

    # localidade relacionada pelo campo 'loc_nu'
    loc = orm.relationship(LogLocalidade,
                           backref=orm.backref('outras_denominacoes'))

    # ordem da denominação
    val_nu = sa.Column(sa.Integer, autoincrement=False, primary_key=True)

    # denominação
    val_tx = sa.Column(sa.Unicode(72))


class LogFaixaLocalidade(Base):
    """
        faixa de CEP das localidades codificadas por logradouro

        esta tabela contém faixas de CEPs das localidades codificadas
        por logradouro (loc_in_sit = 1)
    """
    __tablename__ = 'log_faixa_localidade'

    # chave da localidade
    loc_nu = sa.Column(sa.Integer,
                       sa.ForeignKey(LogLocalidade.loc_nu, ondelete='CASCADE'),
                       primary_key=True)

    # localidade relacionada pelo campo 'loc_nu'
    loc = orm.relationship(LogLocalidade, backref=orm.backref('faixas'))

    # CEP inicial da localidade
    loc_cep_ini = sa.Column(sa.Unicode(8), primary_key=True, index=True)

    # CEP final da localidade
    loc_cep_fim = sa.Column(sa.Unicode(8), index=True)


class LogBairro(Base):
    """
        bairros
    """
    __tablename__ = 'log_bairro'

    # chave do bairro
    bai_nu = sa.Column(sa.Integer, primary_key=True)

    # sigla da UF
    ufe_sg = sa.Column(sa.Unicode(2))

    # chave da localidade
    loc_nu = sa.Column(sa.Integer,
                       sa.ForeignKey(LogLocalidade.loc_nu, ondelete='CASCADE'))

    # localidade relacionada pelo campo 'loc_nu'
    loc = orm.relationship(LogLocalidade, backref=orm.backref('bairros'))

    # nome do bairro
    bai_no = sa.Column(sa.Unicode(72))

    # abreviatura do nome do bairro
    bai_no_abrev = sa.Column(sa.Unicode(36), nullable=True)


class LogVarBai(Base):
    """
        outras denominações do bairro localidade
        (denominação popular, denominação anterior)
    """
    __tablename__ = 'log_var_bai'

    # chave do bairro
    bai_nu = sa.Column(sa.Integer,
                       sa.ForeignKey(LogBairro.bai_nu, ondelete='CASCADE'),
                       primary_key=True)

    # ordem da denominação
    vdb_nu = sa.Column(sa.Integer, autoincrement=False, primary_key=True)

    # bairro relacionado pelo campo 'bai_nu'
    bai = orm.relationship(LogBairro, backref=orm.backref('variacoes'))

    # denominação
    vdb_tx = sa.Column(sa.Unicode(72))


class LogFaixaBairro(Base):
    """
        faixa de CEP de bairro
    """
    __tablename__ = 'log_faixa_bairro'

    # chave do bairro
    bai_nu = sa.Column(sa.Integer,
                       sa.ForeignKey(LogBairro.bai_nu, ondelete='CASCADE'),
                       primary_key=True)

    # bairro relacionado pelo campo 'bai_nu'
    bai = orm.relationship(LogBairro, backref=orm.backref('faixas'))

    # CEP inicial do bairro
    fcb_cep_ini = sa.Column(sa.Unicode(8), primary_key=True, index=True)

    # CEP final do bairro
    fcb_cep_fim = sa.Column(sa.Unicode(8), index=True)


class LogCpc(Base):
    """
        caixas postais comunitárias (CPC)

        são áreas rurais e/ou urbanas periféricas não atendidas
        pela distribuição domiciliária
    """
    __tablename__ = 'log_cpc'

    # chave da caixa postal comunitária
    cpc_nu = sa.Column(sa.Integer, primary_key=True)

    # sigla da UF
    ufe_sg = sa.Column(sa.Unicode(2))

    # chave da localidade
    loc_nu = sa.Column(sa.Integer,
                       sa.ForeignKey(LogLocalidade.loc_nu, ondelete='CASCADE'))

    # localidade relacionada pelo campo 'loc_nu'
    loc = orm.relationship(LogLocalidade, backref=orm.backref('cpcs'))

    # nome da CPC
    cpc_no = sa.Column(sa.Unicode(72))

    # endereço da CPC
    cpc_endereco = sa.Column(sa.Unicode(100))

    # CEP da CPC
    cep = sa.Column(sa.Unicode(8), index=True)


class LogFaixaCpc(Base):
    """
        faixa de caixa postal comunitária
    """
    __tablename__ = 'log_faixa_cpc'

    # chave da caixa postal comunitária
    cpc_nu = sa.Column(sa.Integer,
                       sa.ForeignKey(LogCpc.cpc_nu, ondelete='CASCADE'),
                       primary_key=True)

    # número inicial da caixa postal comunitária
    cpc_inicial = sa.Column(sa.Unicode(6), primary_key=True)

    # número final da caixa postal comunitária
    cpc_final = sa.Column(sa.Unicode(6))


class LogLogradouro(Base):
    """
        logradouros

        contém os registros das localidades codificadas por logradouro
        (loc_in_sit = 1)

        para encontrar o bairro, deve ser utilizado o campo 'bai_nu_ini'
        o campo 'bai_nu_fim' está sendo desativado
    """
    __tablename__ = 'log_logradouro'

    # chave do logradouro
    log_nu = sa.Column(sa.Integer, primary_key=True)

    # sigla da UF
    ufe_sg = sa.Column(sa.Unicode(2))

    # chave da localidade
    loc_nu = sa.Column(sa.Integer,
                       sa.ForeignKey(LogLocalidade.loc_nu, ondelete='CASCADE'))

    # localidade relacionada pelo campo 'loc_nu'
    loc = orm.relationship(LogLocalidade, backref=orm.backref('logradouros'))

    # chave do bairro inicial do logradouro
    bai_nu_ini = sa.Column(sa.Integer,
                           sa.ForeignKey(LogBairro.bai_nu, ondelete='CASCADE'))

    # bairro relacionado pelo campo 'bai_nu_ini'
    bai_ini = orm.relationship(LogBairro, backref=orm.backref('logradouros'))

    # chave do bairro final do logradouro (obsoleto)
    bai_nu_fim = sa.Column(sa.Integer, nullable=True)

    # nome do logradouro
    log_no = sa.Column(sa.Unicode(100))

    # complemento do logradouro
    log_complemento = sa.Column(sa.Unicode(100), nullable=True)

    # CEP do logradouro
    cep = sa.Column(sa.Unicode(8), index=True)

    # tipo de logradouro
    tlo_tx = sa.Column(sa.Unicode(36))

    # indicador de utilização do tipo de logradouro (S/N)
    log_sta_tlo = sa.Column(sa.Unicode(1), nullable=True)

    # abreviatura do nome do logradouro
    log_no_abrev = sa.Column(sa.Unicode(36), nullable=True)


class LogVarLog(Base):
    """
        outras denominações do logradouro
        (denominação popular, denominação anterior)
    """
    __tablename__ = 'log_var_log'

    # chave do logradouro
    log_nu = sa.Column(sa.Integer,
                       sa.ForeignKey(LogLogradouro.log_nu, ondelete='CASCADE'),
                       primary_key=True)

    # ordem da denominação
    vlo_num = sa.Column(sa.Integer,
                        autoincrement=False,
                        primary_key=True)

    # tipo de logradouro da variação
    tlo_tx = sa.Column(sa.Unicode(36))

    # noma da variação do logradouro
    vlo_tx = sa.Column(sa.Unicode(150))


class LogNumSec(Base):
    """
        faixa numérica do seccionamento
    """
    __tablename__ = 'log_num_sec'

    # chave do logradouro
    log_nu = sa.Column(sa.Integer,
                       sa.ForeignKey(LogLogradouro.log_nu, ondelete='CASCADE'),
                       primary_key=True)

    # número inicial do seccionamento
    sec_nu_ini = sa.Column(sa.Unicode(10), primary_key=True)

    # número final do seccionamento
    sec_nu_fim = sa.Column(sa.Unicode(10))

    # indica a paridade/lado do seccionamento
    # A - ambos
    # P - par
    # I - ímpar
    # D - direito
    # E - esquerdo
    sec_in_lado = sa.Column(sa.Unicode(1))


class LogGrandeUsuario(Base):
    """
        clientes com grande volume postal
        (empresas, universidades, bancos, orgãos públicos etc)

        o campo 'log_nu' está vazio para as localidades não codificadas
        (loc_in_sit = 0)

        devendo ser utilizado o campo 'gru_endereco' para endereçamento
    """
    __tablename__ = 'log_grande_usuario'

    # chave do grande usuário
    gru_num = sa.Column(sa.Integer, primary_key=True)

    # sigla da UF
    ufe_sg = sa.Column(sa.Unicode(2))

    # chave da localidade
    loc_nu = sa.Column(sa.Integer,
                       sa.ForeignKey(LogLocalidade.loc_nu, ondelete='CASCADE'),
                       nullable=True)

    # localidade relacionada pelo campo 'loc_nu'
    loc = orm.relationship(LogLocalidade,
                           backref=orm.backref('grandes_usuarios'))

    # chave do bairro
    bai_nu = sa.Column(sa.Integer,
                       sa.ForeignKey(LogBairro.bai_nu, ondelete='CASCADE'))

    # bairro relacionado pelo campo 'bai_nu'
    bai = orm.relationship(LogBairro, backref=orm.backref('grandes_usuarios'))

    # chave do logradouro
    log_nu = sa.Column(
        sa.Integer, sa.ForeignKey(LogLogradouro.log_nu, ondelete='CASCADE'), nullable=True)

    # nome do grande usuário
    gru_no = sa.Column(sa.Unicode(72))

    # endereço do grande usuário
    gru_endereco = sa.Column(sa.Unicode(100))

    # CEP do grande usuário
    cep = sa.Column(sa.Unicode(8), index=True)

    # abreviatura do nome do grande usuário
    gru_no_abrev = sa.Column(sa.Unicode(36), nullable=True)


class LogUnidOper(Base):
    """
        unidades operacionais dos correios
        são agências próprias ou terceirizadas, centros de distribuição etc

        o campo 'log_nu' está vazio para as localidades não codificadas
        (loc_in_sit = 0)

        devendo ser utilizado o campo 'uop_endereco' para endereçamento
    """
    __tablename__ = 'log_unid_oper'

    # chave da UOP
    uop_num = sa.Column(sa.Integer, primary_key=True)

    # sigla da UF
    ufe_sg = sa.Column(sa.Unicode(2))

    # chave da localidade
    loc_nu = sa.Column(sa.Integer,
                       sa.ForeignKey(LogLocalidade.loc_nu, ondelete='CASCADE'))

    # localidade relacionada pelo campo 'loc_nu'
    loc = orm.relationship(LogLocalidade, backref=orm.backref('uops'))

    # chave do bairro
    bai_nu = sa.Column(sa.Integer,
                       sa.ForeignKey(LogBairro.bai_nu, ondelete='CASCADE'))

    # bairro relacionado pelo campo 'bai_nu'
    bai = orm.relationship(LogBairro, backref=orm.backref('uops'))

    # chave do logradouro
    log_nu = sa.Column(sa.Integer,
                       sa.ForeignKey(LogLogradouro.log_nu, ondelete='CASCADE'),
                       nullable=True)

    # nome da UOP
    uop_no = sa.Column(sa.Unicode(100))

    # endereço da UOP
    uop_endereco = sa.Column(sa.Unicode(100))

    # CEP da UOP
    cep = sa.Column(sa.Unicode(8), index=True)

    # indicador de caixa postal (S/N)
    uop_in_cp = sa.Column(sa.Unicode(1))

    # abreviatura do nome da unidade operacional
    uop_no_abrev = sa.Column(sa.Unicode(36), nullable=True)


class LogFaixaUop(Base):
    """
        faixa de caixa postal - UOP
    """
    __tablename__ = 'log_faixa_uop'

    # chave da UOP
    uop_num = sa.Column(sa.Integer, primary_key=True)

    # número inicial da caixa postal
    fnc_inicial = sa.Column(sa.Unicode(6), primary_key=True)

    # número final da caixa postal
    fnc_final = sa.Column(sa.Unicode(6))
