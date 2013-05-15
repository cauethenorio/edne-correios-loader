# coding: utf-8

import sqlalchemy as sa

from . import alchemy_utils
from .tabelas import *


class CepUnificado(Base):
    __tablename__ = 'cep_unificado'

    uf = sa.Column(sa.Unicode(2))

    # nome da localidade
    municipio = sa.Column(sa.Unicode(72))
    cod_ibge = sa.Column(sa.Unicode(7), nullable=True)

    bairro = sa.Column(sa.Unicode(72))

    # CEP da localidade não codificada (cidade com um CEP só)
    cep = sa.Column(sa.Unicode(8), primary_key=True)

    precisao = sa.Column(sa.Unicode(16))
    tipo = sa.Column(sa.Unicode(36))
    nome = sa.Column(sa.Unicode(100))
    complemento = sa.Column(sa.Unicode(100), nullable=True)

engine = alchemy_utils.cria_engine('mysql', 'localhost', 'root',
                                   '', 'cep2', echo=True)

Base.metadata.create_all(engine)

sessao = sa.orm.sessionmaker(bind=engine)()

logradouros = (sessao.query(
    LogLogradouro.ufe_sg.label('uf'),
    LogLocalidade.loc_no.label('municipio'),
    LogLocalidade.mun_nu.label('cod_ibge'),
    LogBairro.bai_no.label('bairro'),
    LogLogradouro.cep.label('cep'),
    sa.sql.expression.literal_column('"logradouro"').label('precisao'),
    LogLogradouro.tlo_tx.label('tipo'),
    LogLogradouro.log_no.label('nome'),
    LogLogradouro.log_complemento.label('complemento')
)
    .join(LogBairro)
    .join(LogLocalidade, LogLogradouro.loc_nu == LogLocalidade.loc_nu))


localidades = (sessao.query(
    LogLocalidade.ufe_sg.label('uf'),
    LogLocalidade.loc_no.label('municipio'),
    LogLocalidade.mun_nu.label('cod_ibge'),
    #LogBairro.bai_no.label('bairro'),
    sa.sql.expression.null().label('bairro'),
    LogLocalidade.cep.label('cep'),
    sa.sql.expression.literal_column('"localidade"').label('precisao'),
    sa.sql.expression.null().label('tipo'),
    sa.sql.expression.null().label('nome'),
    sa.sql.expression.null().label('complemento')
)
    .filter(LogLocalidade.cep != None))
    #.join(LogBairro))

union_query = logradouros.union(localidades)

from sqlalchemy.sql.expression import Executable, ClauseElement
from sqlalchemy.ext.compiler import compiles


class InsertFromSelect(Executable, ClauseElement):
    _execution_options = \
        Executable._execution_options.union({'autocommit': True})

    def __init__(self, table, select):
        self.table = table
        self.select = select


@compiles(InsertFromSelect)
def visit_insert_from_select(element, compiler, **kw):
    return "INSERT INTO %s (%s)" % (
        compiler.process(element.table, asfrom=True),
        compiler.process(element.select)
    )

insert = InsertFromSelect(CepUnificado.__table__, union_query.statement)

engine.execute(insert)