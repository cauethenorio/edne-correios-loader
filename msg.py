from __future__ import print_function

import sys

identacao = 0
largura_fixa = 50


def exibe(mensagem, valor='', start='', end='\n'):

    print(start, end='')
    print(" " * identacao, end='')

    padrao = "{:%ss}" % (largura_fixa - identacao - len(str(valor)))
    print(padrao.format(mensagem), end='')
    print('{} '.format(str(valor)), end=end)
    sys.stdout.flush()