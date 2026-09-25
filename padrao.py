#!/usr/bin/env python3
"""O CONJUNTO PADRAO do OLED do D-Sig — fonte unica de verdade da arte.

Deste arquivo saem tres coisas, e por isso nao pode haver uma quarta descricao da mesma
geometria em lugar nenhum:
  1. os PNGs de revisao (para eu olhar e para o usuario aprovar);
  2. o const image do timbre (a unica imagem que sobrou);
  3. o corpo das funcoes de tela em line_oled/rect_oled/print, para entrar no
     Update_OLED do D-Sig.fonte.gpc.

AS TELAS, e onde cada uma vive no script:
  identidade   CurrentMode == 0  — nenhum dominio ativo
  dominio      CurrentMode == 1..4
  status       MenuLevel > 0     — o menu do OPTIONS

A DECISAO DE DESENHO que manda em tudo: o motivo do sinal (a linha com quatro
derivacoes) aparece SO onde carrega informacao — no dominio, mostrando qual saida esta
ativa, e no status, mostrando o sinal cortado. Na tela de identidade ele seria papel de
parede, e papel de parede em 128x64 e desperdicio de um espaco que nao tem.

A CONFERENCIA DE FAIXAS DE TEXTO NAO ESTA AQUI, e isso e decisao.
O print com fundo 1 pinta fundo preto proprio e APAGA o que estiver embaixo, entao
desenhar na faixa de um texto e desperdicio invisivel. A checagem que impede isso mora
no embutir.py, que a roda em TODA publicacao lendo o D-Sig.gpc publicado — as faixas
saem dos print das funcoes de tela, e a arte sai dos line_oled/rect_oled/image_oled das
mesmas funcoes. Fonte unica, no artefato real, no momento em que ele vai para o ar.

Este arquivo ja teve essa conferencia, apoiada num faixas.py que lia o Update_OLED. Duas
coisas a mataram, e as duas valem registro:
  1. a primeira versao tinha as faixas DIGITADAS por mim — duas, onde o script imprimia
     quatro linhas de nome de jogo. Ela rodou, passou, e aprovou 343 pixels de desenho
     que o print ia apagar. Conferencia vale o que vale o dado que a alimenta;
  2. corrigida para LER do script, ela passou a ler o Update_OLED — e nesta mesma
     alteracao os print sairam do Update_OLED para as funcoes de tela. A ferramenta
     ficou lendo uma estrutura que eu acabara de desmontar, e quebrou.
Duas checagens da mesma coisa, uma delas lendo um artefato intermediario, e pior que
uma. A que ficou e a que le o que vai para o ar.
"""
from PIL import Image, ImageDraw, ImageFont
import os, sys, json

L, A = 128, 64
BR, PR = 1, 0
SAI = os.path.dirname(os.path.abspath(__file__))
fonte = ImageFont.load_default()
_med = ImageDraw.Draw(Image.new('1', (400, 60)))

# Alturas da fonte do OLED, para simular o print nos PNGs de revisao.
ALT_OLED = {0: 10, 1: 17}


def medir(s, esc=1):
    b = _med.textbbox((0, 0), s, font=fonte)
    return (b[2] - b[0]) * esc, (b[3] - b[1]) * esc


def texto(im, x, y, s, esc=1, inv=False):
    b = _med.textbbox((0, 0), s, font=fonte)
    tmp = Image.new('1', (b[2] + 2, b[3] + 2), BR if inv else PR)
    ImageDraw.Draw(tmp).text((0, 0), s, fill=PR if inv else BR, font=fonte)
    tmp = tmp.crop((0, b[1], b[2] + 2, b[3]))
    if esc > 1:
        tmp = tmp.resize((tmp.width * esc, tmp.height * esc), Image.NEAREST)
    im.paste(tmp, (x, y))
    return tmp.size


# ============================================================== 1. o timbre (imagem)
# A UNICA imagem do conjunto, e ela se justifica sozinha: o print tem fonte 0 (10px) e
# fonte 1 (17px), e este "D-Sig" tem 30px. Nao existe sequencia de linha e retangulo
# que o desenhe por menos que os ~390 bytes que ele custa.
TIMBRE_Y = 2


def timbre():
    im = Image.new('1', (L, A), PR)
    w, _ = medir('D-Sig', 3)
    texto(im, (L - w) // 2, TIMBRE_Y, 'D-Sig', esc=3)
    return im


# ======================================================== 2. a geometria (primitivas)
# ('lin', x0,y0,x1,y1) | ('ret', x,y,larg,alt,cheio) | ('txt', x,y,'STR',tam[,inv])

def derivacao(x, y, larg, ativo=0, simbolico=False):
    """Linha de sinal com quatro derivacoes. Cabe em 11px de altura."""
    ops = [('lin', x, y, x + larg, y), ('ret', x, y - 2, 4, 5, 1)]
    passo = (larg - 12) // 4
    for i in range(4):
        xt = x + 10 + i * passo
        ops.append(('lin', xt, y, xt, y + 4))
        if simbolico:
            cheio = f'Igual(n, {i+1})'
        else:
            cheio = 1 if (ativo == 0 or ativo == i + 1) else 0
        ops.append(('ret', xt - 3, y + 4, 7, 6, cheio))
    return ops


def ops_identidade():
    """CurrentMode == 0. O timbre em cima, regua, e o nome do jogo em duas linhas.
    As linhas 3 e 4 do nome sairam do script: o app sempre gravou "" nelas (corta o
    nome em 20 caracteres), entao reservavam y 35..59 para nunca mostrar nada. Era
    esse espaco morto que a tela de identidade precisava."""
    return [('lin', 4, 34, 123, 34),
            ('nome', 4, 37, 'GAME_NAME_1', 0),
            ('nome', 4, 49, 'GAME_NAME_2', 0)]


def ops_dominio(n, simbolico=False):
    """CurrentMode == n. O script imprime o nome do dominio em x>=12, y 25..41.
    A faixa de cima e o que interessa: quatro blocos, o ativo em video invertido. Da
    para saber em que dominio se esta SEM LER NADA — util no meio do jogo, que e quando
    se troca de dominio. O rodape repete na linguagem do sinal: so a derivacao ativa
    cheia. A mesma coisa em duas linguagens, de proposito — o bloco e para quem conta,
    a derivacao e para quem reconhece a forma.
    Se o print nao conseguir letra preta sobre branco, o bloco ativo fica um retangulo
    branco sem algarismo — e continua lendo, porque os outros tres tem numero e a
    posicao diz qual e. O desenho nao depende dessa resposta."""
    ops = []
    for i in range(4):
        x0 = 9 + i * 29
        # SIMBOLICO e o modo que gera a funcao PARAMETRIZADA para o script: em vez de
        # 1/0 fixos, sai Igual(n, k) — e por isso os quatro dominios sao uma funcao e
        # nao quatro. Foi esse parametro que fez a diferenca de 3.488 para 252 bytes.
        ativo = f'Igual(n, {i+1})' if simbolico else (1 if i + 1 == n else 0)
        ops.append(('ret', x0, 4, 23, 15, ativo))
        ops.append(('txt', x0 + 9, 7, str(i + 1), 0, ativo))
    ops += [('lin', 4, 22, 123, 22), ('lin', 4, 45, 123, 45),
            ('txt', 4, 48, 'D-Sig', 0)]
    return ops + derivacao(50, 52, 72, ativo=n, simbolico=simbolico)


def ops_status():
    """MenuLevel > 0. O script imprime MENU_TITLE em y 10..26 e a versao em y 36..45.
    Sobram tres faixas estreitas: y 1..9, y 27..35 e y 46..62, e nenhuma cabe a fonte
    de 11px — foi tentar por um rotulo em y=1 que fez a primeira versao invadir o
    titulo. Entao nao ha rotulo: quem diz o que e a tela ja e o texto do script.
    O que a imagem acrescenta e o SIGNIFICADO — o menu de status congela os MODs, e o
    motivo mostra o sinal interrompido: a entrada chega, o no esta la, o corte, e as
    quatro saidas VAZIAS."""
    ye = 56
    ops = [('lin', 4, 5, 123, 5), ('lin', 4, 31, 123, 31), ('lin', 4, 49, 123, 49),
           ('lin', 6, ye, 16, ye), ('ret', 16, ye - 2, 5, 5, 1),
           ('lin', 25, ye - 5, 33, ye + 5), ('lin', 33, ye - 5, 25, ye + 5)]
    for i in range(4):
        ops.append(('ret', 40 + i * 23, ye - 3, 13, 7, 0))
    return ops


TELAS = [('identidade', ops_identidade(), 'repouso'),
         ('status', ops_status(), 'status')] + \
        [(f'dominio-{n}', ops_dominio(n), 'dominio') for n in (1, 2, 3, 4)]


# ------------------------------------------------------------------ render e GPC
def render(ops, com_timbre=False, nomes=('CYBERPUNK', ' 2077'), moldura=True):
    im = timbre() if com_timbre else Image.new('1', (L, A), PR)
    d = ImageDraw.Draw(im)
    if moldura:
        d.rectangle([0, 0, L - 1, A - 1], outline=BR)    # a moldura e do script
    for op in ops:
        if op[0] == 'lin':
            d.line([(op[1], op[2]), (op[3], op[4])], fill=BR)
        elif op[0] == 'ret':
            _, x, y, w, h, cheio = op
            d.rectangle([x, y, x + w - 1, y + h - 1],
                        fill=BR if cheio else PR, outline=BR)
        elif op[0] == 'nome':                            # simula o print do script
            _, x, y, var, tam = op
            texto(im, x, y, nomes[0] if var.endswith('1') else nomes[1])
        else:
            _, x, y, s, tam = op[:5]
            texto(im, x, y, s, inv=len(op) > 5 and op[5])
    return im


def gpc(ops, ind='        '):
    out, textos = [], {}
    for op in ops:
        if op[0] == 'lin':
            out.append(f'{ind}line_oled({op[1]}, {op[2]}, {op[3]}, {op[4]}, 1, 1);')
        elif op[0] == 'ret':
            _, x, y, w, h, cheio = op
            out.append(f'{ind}rect_oled({x}, {y}, {w}, {h}, {cheio}, 1);')
        elif op[0] == 'nome':
            _, x, y, var, tam = op
            out.append(f'{ind}print({x}, {y}, {tam}, 1, {var}[0]);')
        else:
            _, x, y, s, tam = op[:5]
            inv = op[5] if len(op) > 5 else 0
            v = 'DS_TITULO' if s == 'D-Sig' else 'DS_N' + s
            textos[v] = s
            # fundo 1 = fundo preto, letra branca; no bloco ativo (branco) isso
            # pintaria um retangulo preto por cima, daí fundo 0 quando invertido.
            fundo = f'1 - {inv}' if isinstance(inv, str) else (0 if inv else 1)
            out.append(f'{ind}print({x}, {y}, {tam}, {fundo}, {v}[0]);')
    return out, textos


# ---------------------------------------------------------------- CONFERENCIA
if __name__ == '__main__':
    # Gera o timbre.png (insumo do png2gpc.py) e a folha de revisao. A verificacao de
    # faixas de texto e do embutir.py — ver o cabecalho deste arquivo.
    timbre().save(os.path.join(SAI, 'timbre.png'))
    pecas = [(render(ops, com_timbre=(nome == 'identidade')), nome)
             for nome, ops, _ in TELAS]
    for im, nome in pecas:
        im.save(os.path.join(SAI, f'p-{nome}.png'))

    esc, cols = 5, 2
    linhas = (len(pecas) + 1) // 2
    folha = Image.new('1', (cols * (L * esc + 12) + 12,
                            linhas * (A * esc + 26) + 12), PR)
    fd = ImageDraw.Draw(folha)
    for i, (im, nome) in enumerate(pecas):
        cx = 12 + (i % cols) * (L * esc + 12)
        cy = 12 + (i // cols) * (A * esc + 26)
        fd.text((cx, cy), nome, fill=BR, font=fonte)
        folha.paste(im.resize((L * esc, A * esc), Image.NEAREST), (cx, cy + 14))
    folha.save(os.path.join(SAI, 'p-folha.png'))

    print(f'{len(pecas)} telas 128x64 em 1 bit + timbre.png')
    for nome, ops, _ in TELAS:
        n = len([o for o in ops if o[0] in ('lin', 'ret', 'txt', 'nome')])
        print(f'  {nome:11s} {n:3d} chamadas de desenho')
    uni = sum(len([o for o in ops if o[0] in ('lin', 'ret', 'txt', 'nome')])
              for nome, ops, _ in TELAS if not nome.startswith('dominio-2')
              and not nome.startswith('dominio-3') and not nome.startswith('dominio-4'))
    print(f'  no script os 4 dominios sao UMA funcao: {uni} chamadas de fato')
