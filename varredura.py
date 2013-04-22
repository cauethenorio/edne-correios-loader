# coding: utf-8

import os
import fnmatch

from edne2db import dados
from edne2db import padroes_arquivos


def compara(arquivo, padrao):
    return fnmatch.fnmatch(arquivo.lower(), padrao.lower())


def contem_edne_basico(arquivos):
    padroes = padroes_arquivos.BASICO

    padroes_encontrados = {}
    for nome_padrao, padrao in padroes.items():
        padroes_encontrados[nome_padrao] = []
        for arquivo in arquivos:
            if compara(arquivo, padrao):
                padroes_encontrados[nome_padrao].append(arquivo)

    if [] in padroes_encontrados.values():
        return False

    return padroes_encontrados


def contem_edne_delta(arquivos):

    padroes = {
        key: '{}{}'.format(padroes_arquivos.PREFIXO_DELTA, val).replace('_*', '')
        for key, val in padroes_arquivos.BASICO.items()
    }

    padroes_encontrados = {}
    for nome_padrao, padrao in padroes.items():
        padroes_encontrados[nome_padrao] = []
        for arquivo in arquivos:
            if compara(arquivo, padrao):
                padroes_encontrados[nome_padrao].append(arquivo)

    if all(p == [] for p in padroes_encontrados.values()):
        return False

    return padroes_encontrados


def cria_leitores_dados(dirdados):

    return {
        padrao: dados.ArquivoDados(dirdados['caminho'], arquivos)
        for padrao, arquivos in dirdados['padroes'].items()
    }


def busca_recursiva(caminho_raiz):

    dirs_encontrados = {
        'basico': [],
        'delta': []
    }

    varreduras = {
        'basico': contem_edne_basico,
        'delta': contem_edne_delta,
    }

    for caminho, diretorios, arquivos in os.walk(caminho_raiz):
        for tipo, func_varredura in varreduras.items():

            padroes = func_varredura(arquivos)

            if padroes:
                dirs_encontrados[tipo].append({
                    'caminho': caminho,
                    'padroes': padroes
                })

    if len(dirs_encontrados['basico']):
        dirs_encontrados['basico'] = dirs_encontrados['basico'][0]

    return dirs_encontrados