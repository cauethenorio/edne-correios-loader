# coding: utf-8

import sqlalchemy as sa

from edne2db import tabelas
from edne2db import msg


def cria_engine(dialeto, servidor, usuario, senha, banco, porta='',
                driver='', echo=False):

    porta = ':{}'.format(porta) if porta else porta
    driver = '+{}'.format(driver) if driver else driver

    string_conexao =\
        '{dialeto}{driver}://{usuario}:{senha}@{servidor}{porta}/{banco}'\
            .format(**locals())

    return sa.create_engine(string_conexao, echo=echo)


def testa_conexao(engine):
    try:
        connection = engine.connect()
        connection.close()
        return True
    except sa.exc.OperationalError:
        return False


def monta_dict(Tabela, dados, campos=True, chaves=False):

    campos_dict = {}
    chaves_dict = {}

    for idx, campo in enumerate(Tabela.__table__.columns):

        if dados[idx]:
            valor = campo.type.python_type(dados[idx])

            if campos:
                campos_dict[campo.name] = valor

            if campo.primary_key and chaves:
                chaves_dict[campo.name] = valor

    if campos and chaves:
        return {'campos': campos_dict, 'chaves': chaves_dict}

    if campos:
        return campos_dict
    if chaves:
        return chaves_dict


def insere(session, Tabela, dados):
    instancia = Tabela()

    for idx, campo in enumerate(Tabela.__table__.columns):

        if dados[idx]:
            dados[idx] = campo.type.python_type(dados[idx])
            setattr(instancia, campo.name, dados[idx])

    session.add(instancia)


def atualiza(session, Tabela, dados):
    dicts = monta_dict(Tabela, dados, campos=True, chaves=True)
    session.query(Tabela).filter_by(**dicts['chaves']).update(dicts['campos'])


def remove(session, Tabela, dados):
    dict_chaves = monta_dict(Tabela, dados, campos=False, chaves=True)
    session.query(Tabela).filter_by(**dict_chaves).delete()


operacoes = {
    'INS': insere,
    'UPD': atualiza,
    'DEL': remove,
}


def executa(session, Tabela, dados):
    num_colunas = len(Tabela.__table__.columns)

    operacao = 'INS'
    if len(dados) != num_colunas:
        operacao = dados[len(Tabela.__table__.columns):][0]

    operacoes[operacao](session, Tabela, dados)


def processa_tabelas(mapa_leitores, sessao, envia_a_cada=1000):

    for nome_tabela in tabelas.ordem:
        contador = 0

        Tabela = getattr(tabelas, nome_tabela)
        leitor = mapa_leitores[nome_tabela]

        if not leitor.tem_dados():
            continue

        msg_tabela = 'Populando tabela {}...'.format(nome_tabela)
        msg.exibe(msg_tabela, start='\r', end='')

        try:
            for linha in leitor.registros():
                executa(sessao, Tabela, linha)
                contador += 1

                # define a cada quantos registros é feito o INSERT
                # pode ser aumentado para melhorar a performance
                # ou diminuído para reduzir a memória utilizada
                if contador % envia_a_cada == 0:
                    sessao.flush()
                    msg.exibe(msg_tabela, contador, start='\r', end='')

            sessao.commit()
            msg.exibe(msg_tabela, contador, start='\r', end='')
            print('OK')

        except sa.exc.IntegrityError:
            sessao.rollback()
            print('DADOS EXISTENTES. IGNORADA')

    print('')
