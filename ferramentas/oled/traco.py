# -*- coding: utf-8 -*-
"""Desenha o traco.png: o D, o raio dentro dele, uma entrada e uma saida.

Ate a 1.0.23 o traco era um PNG sem fonte: foi desenhado numa bancada que nao entrou no
repositorio, e engrossar o D exigiria redesenhar de memoria. Este arquivo e a fonte dele.
O icone.py le o traco.png e aplica a separacao das tres cores; aqui so ha a forma, branca
sobre preto, 512x512.

1.0.24 — O D MAIS GORDO (pedido do Daniel). A espessura do D foi de 26 para 40 px. O raio
cresceu um pouco e a haste da entrada e da saida engrossou junto, para o conjunto nao
parecer um D pesado com enfeites finos. Tudo e parametro abaixo.

uso:  python3 traco.py            grava ferramentas/oled/traco.png
      python3 traco.py <arquivo>  grava onde for dito (para comparar antes)
"""
from PIL import Image, ImageDraw
import math, os, sys

AQUI = os.path.dirname(os.path.abspath(__file__))
S = 4                       # superamostragem do desenho
LADO = 512

ESP_D    = 40               # espessura do D
ESP_FIO  = 30               # espessura da entrada e da saida
RAIO_NO  = 31               # raio dos dois nos
RAIO_K   = 1.12             # tamanho do raio (1.0 = 184 px de altura)
X_HASTE  = 162              # x da haste do D
Y_TOPO, Y_BASE = 108, 404   # extensao vertical do D
X_CENTRO = 238              # centro do arco do D
X_NO_E, X_NO_D = 72, 452    # x dos nos de entrada e de saida


def _linha(d, pts, w):
    pts = [(x * S, y * S) for x, y in pts]
    d.line(pts, fill=255, width=int(w * S), joint='curve')
    r = w * S / 2
    for x, y in pts:                      # pontas e cantos arredondados
        d.ellipse([x - r, y - r, x + r, y + r], fill=255)


def _arco(cx, cy, r, a0, a1, n=96):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / n)),
             cy + r * math.sin(math.radians(a0 + (a1 - a0) * i / n))) for i in range(n + 1)]


def traco():
    im = Image.new('L', (LADO * S, LADO * S), 0)
    d = ImageDraw.Draw(im)
    cy = (Y_TOPO + Y_BASE) / 2.0
    r = (Y_BASE - Y_TOPO) / 2.0
    # o D: haste, topo, arco, base
    _linha(d, [(X_HASTE, Y_TOPO), (X_CENTRO, Y_TOPO)] + _arco(X_CENTRO, cy, r, -90, 90)
           + [(X_HASTE, Y_BASE), (X_HASTE, Y_TOPO)], ESP_D)
    # a entrada e a saida
    _linha(d, [(X_NO_E, cy), (X_HASTE, cy)], ESP_FIO)
    _linha(d, [(X_CENTRO + r, cy), (X_NO_D, cy)], ESP_FIO)
    for x in (X_NO_E, X_NO_D):
        d.ellipse([(x - RAIO_NO) * S, (cy - RAIO_NO) * S, (x + RAIO_NO) * S, (cy + RAIO_NO) * S], fill=255)
    # o raio: um poligono solido, centrado no miolo do D
    cx = (X_HASTE + X_CENTRO + r) / 2.0 + 4
    P = [(18, -92), (-46, 14), (-6, 14), (-22, 92), (46, -18), (4, -18)]
    d.polygon([((cx + x * RAIO_K) * S, (cy + y * RAIO_K) * S) for x, y in P], fill=255)
    return im.resize((LADO, LADO), Image.LANCZOS)


if __name__ == '__main__':
    destino = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, 'traco.png')
    traco().save(destino)
    print('  ' + destino)
