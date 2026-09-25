#!/usr/bin/env python3
"""Extrai do D-Sig.gpc as faixas que o texto ocupa em cada tela do OLED.

POR QUE ISTO EXISTE, e e a correcao de um erro meu: o gerar.py tinha as faixas num
dicionario que eu DIGITEI, olhando o script. Digitei duas faixas para a tela de repouso
e o script imprime QUATRO linhas de nome de jogo. A CONFERENCIA que eu tinha escrito
para impedir desenho sobre texto rodou contra o dado errado e passou — conferencia vale
o que vale o dado que a alimenta, e dado digitado a mao nao vale.

Agora as faixas saem do proprio script, por leitura das chamadas de print dentro do
Update_OLED. Se alguem mover um print, a faixa se move junto e a conferencia acompanha.

ALTURA DA FONTE: tamanho 0 = 10px, tamanho 1 = 17px. Com fundo 1 o print pinta fundo
preto proprio, ou seja APAGA o que estiver embaixo — e por isso que a faixa e proibida
e nao apenas desaconselhada.
"""
import re, sys, json, os

ALT = {0: 10, 1: 17}

# O publicado pode estar na raiz do repositorio (oled/ e subpasta) ou ao lado, como na
# bancada onde isto foi escrito. Procurar nos dois evita que a ferramenta so funcione
# na pasta de quem a escreveu.
ONDE = ['../D-Sig.gpc', '../dsig/D-Sig.gpc', 'D-Sig.gpc']


def achar():
    aqui = os.path.dirname(os.path.abspath(__file__))
    for p in ONDE:
        c = os.path.join(aqui, p)
        if os.path.exists(c):
            return c
    raise SystemExit(f'D-Sig.gpc nao encontrado. Procurei em: {", ".join(ONDE)}')


def faixas(caminho=None):
    s = open(caminho or achar(), encoding='utf-8').read()
    m = re.search(r'function Update_OLED\(\)\s*\{(.*?)\n\}', s, re.S)
    if not m:
        raise SystemExit('Update_OLED nao encontrado')
    corpo = m.group(1)

    # Interessam as telas sem menu: repouso (CurrentMode == 0) e dominio (1..4).
    # As do MenuDin e do MenuLevel tem retorno proprio e ficam fora deste recorte.
    alvo = corpo[corpo.index('if(MenuLevel > 0)'):]
    out = {}
    for guarda, rotulo in [(r'if\(CurrentMode == 0\)', 'repouso'),
                           (r'if\(CurrentMode == 1\)', 'dominio'),
                           (r'if\(MenuLevel > 0\)', 'status')]:
        # Duas formas de guarda no script, e a primeira versao deste extrator so
        # entendia uma — por isso a tela de dominio saiu vazia, o que teria deixado
        # passar qualquer desenho sobre o nome do dominio:
        #   if(CurrentMode == 0) {        ...varias linhas...  }
        #   if(CurrentMode == 1) print(...);        <- tudo numa linha, sem chaves
        g = re.search(guarda + r'\s*\{(.*?)\n    \}', alvo, re.S) \
            or re.search(guarda + r'(.*)', alvo)
        if not g:
            continue
        b = []
        for x, y, tam, var in re.findall(
                r'print\((\d+),\s*(\d+),\s*(\d+),\s*1,\s*(\w+)\[0\]\)', g.group(1)):
            x, y, tam = int(x), int(y), int(tam)
            b.append({'x': x, 'y': y, 'x1': 127, 'y1': y + ALT[tam] - 1, 'var': var})
        out[rotulo] = b
    return out


if __name__ == '__main__':
    f = faixas(sys.argv[1] if len(sys.argv) > 1 else None)
    for tela, bs in f.items():
        print(f'{tela}:')
        for b in bs:
            print(f"    x {b['x']:3d}..127   y {b['y']:2d}..{b['y1']:2d}   {b['var']}")
    json.dump(f, open('faixas.json', 'w'), indent=2)
