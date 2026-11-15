# -*- coding: utf-8 -*-
"""Gera os icones do D-Sig: o traco com separacao RGB de tres canais.

O EFEITO. Tres copias do mesmo traco, deslocadas a 120 graus uma da outra, somadas
canal a canal: a primeira so no vermelho, a segunda so no verde, a terceira so no azul.
Onde duas se cruzam aparece a secundaria (R+G=amarelo, G+B=ciano, R+B=magenta); onde as
tres se cruzam, branco. E a mesma soma que a luz faz — nao e paleta escolhida a mao.

Ate a 1.0.16 eram DOIS canais (ciano e magenta deslocados em diagonal), o que da um
vulto, nao um prisma: sem o terceiro canal nao existe o branco central nem as tres
secundarias, e o efeito le como sombra colorida.

O TRACO VEM DE traco.png, e nao mais do icone publicado. Ler o traco do proprio icone
tinha dois defeitos: o que esta BRANCO no icone e a INTERSECAO das tres copias, mais
fina que o traco — cada geracao a partir da anterior afinava o desenho —, e qualquer
mudanca de tamanho se aplicaria de novo a cada rodada. O traco.png e o traco original,
512x512, recuperado do canal vermelho do icone da 1.0.17 (deslocado de volta) e
conferido: regenerar com ESCALA = 1 a partir dele devolve aquele icone pixel a pixel.

1.0.19 — O DESENHO CRESCEU. Ocupava 52% do lado do icone, e no maskable (o que o
Android usa na tela inicial) so 32%. ESCALA aumenta o traco e o DESLOCAMENTO JUNTO, na
mesma proporcao: e a razao entre os dois que faz o prisma — crescer so o traco deixaria
a franja colorida relativamente mais fina e o efeito de profundidade encolheria. O
desenho tambem passou a ser CENTRADO pela caixa do traco; estava 24 px a esquerda.

uso:  python3 icone.py            grava os tres PNG na raiz do repositorio
      python3 icone.py <pasta>    grava na pasta dada (para revisar antes)
"""
from PIL import Image, ImageChops, ImageDraw
import numpy as np, math, sys, os

AQUI   = os.path.dirname(os.path.abspath(__file__))
RAIZ   = os.path.dirname(os.path.dirname(AQUI))
FUNDO  = (13, 17, 23)        # #0d1117, o mesmo de sempre
RAIO   = 0.18                # canto arredondado, fracao do lado
DESLOC = 0.014               # deslocamento de cada canal com ESCALA = 1, fracao do lado
ANGULOS = (90, 210, 330)     # R, G, B — 120 graus entre si
ESCALA = 1.22                # tamanho do desenho em relacao ao da 1.0.17
# O maskable e recortado pelo sistema num circulo (ou outra forma) inscrito; a zona que
# nunca e cortada e o circulo de raio 40% do lado. MASK e a fracao do lado que o icone
# inteiro ocupa la dentro, e o __main__ CONFERE que a tinta fica aquem dos 40%.
MASK   = 0.70
ZONA_SEGURA = 0.40
SUPER  = 4                   # superamostragem: o traco e ampliado e re-limiarizado

def traco_mestre():
    return Image.open(os.path.join(AQUI, "traco.png")).convert("L")

def traco_escalado(lado, escala):
    """O traco, ampliado por `escala` e centrado num quadro lado x lado."""
    m = traco_mestre()
    caixa = m.getbbox()
    rec = m.crop(caixa)
    f = lado * SUPER / m.width * escala
    g = rec.resize((max(1, round(rec.width * f)), max(1, round(rec.height * f))), Image.LANCZOS)
    g = g.point(lambda v: 255 if v >= 128 else 0)        # borda nitida outra vez
    q = Image.new("L", (lado * SUPER, lado * SUPER), 0)
    q.paste(g, ((q.width - g.width) // 2, (q.height - g.height) // 2))
    return q.resize((lado, lado), Image.LANCZOS)

def canto(lado, raio):
    """Mascara do quadrado de cantos arredondados."""
    m = Image.new("L", (lado, lado), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, lado-1, lado-1], radius=int(lado*raio), fill=255)
    return m

def icone(lado, escala=ESCALA, com_canto=True, fundo=FUNDO):
    t = traco_escalado(lado, escala)
    d = lado * DESLOC * escala          # o deslocamento acompanha o traco
    canais = []
    for ang in ANGULOS:
        dx = int(round( d * math.cos(math.radians(ang))))
        dy = int(round(-d * math.sin(math.radians(ang))))
        canais.append(ImageChops.offset(t, dx, dy))
    # SOMA ADITIVA: cada copia entra num canal. O branco nasce da sobreposicao,
    # nao de um desenho branco por cima.
    rgb = Image.merge("RGB", canais)
    alvo = Image.new("RGB", (lado, lado), fundo)
    # a uniao dos tres diz onde ha tinta
    uniao = ImageChops.lighter(ImageChops.lighter(canais[0], canais[1]), canais[2])
    alvo.paste(rgb, (0, 0), uniao)
    saida = alvo.convert("RGBA")
    if com_canto:
        saida.putalpha(canto(lado, RAIO))
    return saida

def raio_da_tinta(img, fundo=FUNDO):
    """Maior distancia do centro a um pixel que nao e fundo, como fracao do lado."""
    a = np.array(img.convert("RGB")).astype(int)
    tinta = np.abs(a - np.array(fundo)).sum(axis=2) > 60
    ys, xs = np.where(tinta)
    c = (img.width - 1) / 2.0
    return float(np.sqrt((xs - c) ** 2 + (ys - c) ** 2).max()) / img.width

if __name__ == "__main__":
    destino = sys.argv[1] if len(sys.argv) > 1 else RAIZ
    for lado, nome in ((512, "icone-512.png"), (192, "icone-192.png")):
        icone(lado).save(os.path.join(destino, nome))
        print(f"  {nome}  ({lado}x{lado})")
    # o maskable precisa de margem de seguranca: o fundo vai ate a borda, sem canto, e o
    # icone inteiro entra reduzido a MASK do lado.
    m = Image.new("RGB", (512, 512), FUNDO)
    peq = icone(int(512 * MASK), com_canto=False).convert("RGB")
    m.paste(peq, ((512 - peq.width) // 2, (512 - peq.height) // 2))
    r = raio_da_tinta(m)
    assert r < ZONA_SEGURA - 0.02, (
        f"a tinta do maskable chega a {r:.3f} do lado; a zona segura e {ZONA_SEGURA} — "
        "o sistema cortaria o desenho. Diminua MASK ou ESCALA.")
    m.save(os.path.join(destino, "icone-maskable.png"))
    print(f"  icone-maskable.png  (512x512, tinta ate {r:.3f} do lado; zona segura {ZONA_SEGURA})")
