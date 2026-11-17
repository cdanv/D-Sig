# -*- coding: utf-8 -*-
"""Desenha a mascote do D-Sig: a vespa-marinha.

POR QUE ELA. A vespa-marinha e uma agua-viva em forma de CUBO: quatro lados, e os
tentaculos saem dos quatro cantos — os quatro destinos de um MOD, os quatro dominios. Nao
tem cerebro central: tem um anel nervoso e quatro centros sensoriais, cada um decidindo
por si, que e a ideia dos MODs. E o toque dela e uma descarga, o raio do logo.

ONDE ELA MORA. O icone do app continua sendo o D com o raio, que se le melhor em 48 px.
A mascote aparece onde ha espaco: na tela vazia do app, na tela de Informacoes e no
README. Em tamanho pequeno o rosto some e sobra a silhueta.

O DESENHO. Corpo em cubo arredondado, olhos fechados em arco, o raio no peito e quatro
tentaculos terminando em nos (as saidas). E so a forma, branca sobre preto; as tres cores
sao as do icone.py, com os mesmos parametros do icone do app. Os olhos tem o traco fino
de proposito: ali as tres cores nao chegam a se sobrepor em branco e saem como dois
pequenos arco-iris — e boa parte do carisma dela.

uso:  python3 mascote.py            grava mascote.png na raiz do repositorio
      python3 mascote.py <arquivo>  grava onde for dito
"""
from PIL import Image, ImageDraw
import math, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, AQUI)
import icone as I

S = 4
LADO = 512
ESP_CORPO = 38          # espessura do contorno do corpo
ESP_TENT  = 28          # espessura dos tentaculos
RAIO_NO   = 25          # no na ponta de cada tentaculo
ESP_OLHO  = 16          # traco dos olhos: fino, para as cores nao fecharem em branco
# (x de saida, x de chegada, amplitude da onda, y de chegada) de cada tentaculo
TENTACULOS = ((158, 112, -16, 430), (224, 206, 14, 452), (288, 306, -14, 452), (354, 400, 16, 430))


def _linha(d, pts, w):
    pts = [(x * S, y * S) for x, y in pts]
    d.line(pts, fill=255, width=int(w * S), joint='curve')
    r = w * S / 2
    for x, y in pts:
        d.ellipse([x - r, y - r, x + r, y + r], fill=255)


def _arco(cx, cy, r, a0, a1, n=60):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def _tentaculo(x0, y0, x1, y1, amp, n=40, ondas=1.5):
    return [(x0 + (x1 - x0) * (i / n) + amp * math.sin((i / n) * ondas * 2 * math.pi) * (0.3 + 0.7 * i / n),
             y0 + (y1 - y0) * (i / n)) for i in range(n + 1)]


def traco():
    im = Image.new('L', (LADO * S, LADO * S), 0)
    d = ImageDraw.Draw(im)
    xe, xd, yt, yb, rc = 136, 376, 76, 286, 84
    # o corpo: lados retos, cantos de cima redondos, borda de baixo arqueada para cima
    _linha(d, [(xe, yb)] + _arco(xe + rc, yt + rc, rc, 180, 270)
           + _arco(xd - rc, yt + rc, rc, 270, 360) + [(xd, yb)], ESP_CORPO)
    cx = (xe + xd) / 2.0
    R = (xd - xe) * 1.15
    h = math.sqrt(R * R - ((xd - xe) / 2.0) ** 2)
    a = math.degrees(math.asin(((xd - xe) / 2.0) / R))
    _linha(d, _arco(cx, yb + h, R, 270 - a, 270 + a), ESP_CORPO)
    # os olhos, fechados em arco
    _linha(d, _arco(206, 172, 25, 200, 340), ESP_OLHO)
    _linha(d, _arco(306, 172, 25, 200, 340), ESP_OLHO)
    # o raio no peito
    P = [(18, -92), (-46, 14), (-6, 14), (-22, 92), (46, -18), (4, -18)]
    d.polygon([((256 + x * 0.37) * S, (206 + y * 0.37) * S) for x, y in P], fill=255)
    # os quatro tentaculos, cada um terminando num no
    for x0, x1, amp, y1 in TENTACULOS:
        p = _tentaculo(x0, yb + 4, x1, y1, amp)
        _linha(d, p, ESP_TENT)
        x, y = p[-1]
        d.ellipse([(x - RAIO_NO) * S, (y - RAIO_NO) * S, (x + RAIO_NO) * S, (y + RAIO_NO) * S], fill=255)
    return im.resize((LADO, LADO), Image.LANCZOS)


if __name__ == '__main__':
    destino = sys.argv[1] if len(sys.argv) > 1 else os.path.join(I.RAIZ, 'mascote.png')
    t = traco()
    I.traco_mestre = lambda: t          # as cores sao as do icone, com os mesmos parametros
    I.icone(384).save(destino)
    print('  ' + destino + '  (384x384)')
