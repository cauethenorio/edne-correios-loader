# coding: utf-8

import os


class ArquivoDados(object):

    def __init__(self, dir, arquivos_dados, verbose=True):

        self._dir = dir
        self._verbose = verbose
        self._arquivos_dados = arquivos_dados

    def __repr__(self):
        return u"ArquivoDados({})".format(self._arquivos_dados)

    @staticmethod
    def _limpa_campo(campo):
        return unicode(campo.strip(' \r\n'))

    def _formata_linha(self, linha):
        return [
            self._limpa_campo(campo)
            for campo in linha.decode('latin1').split('@')
        ]

    def tem_dados(self):
        return len(self._arquivos_dados)

    def registros(self):
        for arquivo in self._arquivos_dados:
            with open(os.path.join(self._dir, arquivo), 'r') as f:
                for linha in f:
                    yield self._formata_linha(linha)
