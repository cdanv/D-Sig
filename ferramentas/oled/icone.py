# -*- coding: utf-8 -*-
"""Gera os icones do D-Sig: o traco com separacao RGB de tres canais.

O EFEITO. Tres copias do mesmo traco, deslocadas a 120 graus uma da outra, somadas
canal a canal: a primeira so no vermelho, a segunda so no verde, a terceira so no azul.
Onde duas se cruzam aparece a secundaria (R+G=amarelo, G+B=ciano, R+B=magenta); onde as
tres se cruzam, branco. E a mesma soma que a luz faz — nao e paleta escolhida a mao.

Ate a 1.0.16 eram DOIS canais (ciano e magenta deslocados em diagonal), o que da um
vulto, nao um prisma: sem o terceiro canal nao existe o branco central nem as tres
secundarias, e o efeito le como sombra colorida.

O traco vem do icone publicado — a forma nao muda, so a cor.
"""
from PIL import Image, ImageChops
import numpy as np, math, sys, os

AQUI   = os.path.dirname(os.path.abspath(__file__))
FUNDO  = (13, 17, 23)        # #0d1117, o mesmo de sempre
RAIO   = 0.18                # canto arredondado, fracao do lado
DESLOC = 0.014               # deslocamento de cada canal, fracao do lado
ANGULOS = (90, 210, 330)     # R, G, B — 120 graus entre si

def mascara_do_traco(origem):
    """O traco e o que esta BRANCO no icone publicado."""
    a = np.array(Image.open(origem).convert("RGBA")).astype(int)
    r, g, b, al = a[...,0], a[...,1], a[...,2], a[...,3]
    return Image.fromarray((((r>200)&(g>200)&(b>200)&(al>128))*255).astype('uint8'))

def canto(lado, raio):
    """Mascara do quadrado de cantos arredondados."""
    from PIL import ImageDraw
    m = Image.new("L", (lado, lado), 0)
    ImageDraw.Draw(m).rounded_rectangle([0, 0, lado-1, lado-1], radius=int(lado*raio), fill=255)
    return m

def icone(traco, lado, desloc=DESLOC, com_canto=True, fundo=FUNDO):
    t = traco.resize((lado, lado), Image.LANCZOS)
    d = lado * desloc
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

if __name__ == "__main__":
    origem = sys.argv[1] if len(sys.argv) > 1 else os.path.join(AQUI, "icone-512.png")
    traco = mascara_do_traco(origem)
    for lado, nome in ((512, "icone-512.png"), (192, "icone-192.png")):
        icone(traco, lado).save(os.path.join(AQUI, "novo-" + nome))
        print(f"  novo-{nome}  ({lado}x{lado})")
    # o maskable precisa de margem de seguranca: o sistema recorta um circulo
    # inscrito, entao o traco encolhe para 62% e o fundo vai ate a borda, sem canto.
    m = Image.new("RGB", (512, 512), FUNDO)
    peq = icone(traco, int(512*0.62), com_canto=False).convert("RGB")
    m.paste(peq, ((512-peq.width)//2, (512-peq.height)//2))
    m.save(os.path.join(AQUI, "novo-icone-maskable.png"))
    print("  novo-icone-maskable.png  (512x512, traco a 62% pela zona segura)")
