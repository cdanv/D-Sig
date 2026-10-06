#!/usr/bin/env python3
"""PNG 1 bit -> 'const image' do GPC, no formato exato do Export do OLED Studio.

O FORMATO, dito pelo compilador, que e a unica fonte que nao erra:
  const image nome[] = { {larg, alt, b0, b1, ...} };
  - o numero de valores e 2 + ceil(larg * alt / 8) — mensagem GPC5116;
  - portanto FLUXO CONTINUO de bits, na ordem de varredura (x primeiro, depois y),
    SEM enchimento no fim de linha: a linha seguinte comeca no bit em que a anterior
    parou, no meio do byte se for o caso;
  - MSB primeiro: o bit 7 do primeiro byte e o pixel (0,0);
  - desenha com image_oled(x, y, cor, ?, nome[0]).

O ERRO QUE ESTA AQUI DE PROPOSITO COMO LEMBRETE: a primeira versao empacotava
ceil(larg/8) bytes POR LINHA, e eu a declarei provada porque reproduziu, byte a byte,
o Export do OLED Studio. Reproduziu mesmo — mas o caso era o marca, de 104 de largura,
e 104 e multiplo de 8: com largura multipla de 8 as duas formulas dao o MESMO
resultado. O teste nao separava as hipoteses. Daí a conferencia abaixo exigir agora um
caso de largura NAO multipla de 8 para se dizer conclusiva.

POR QUE RECORTAR NA CAIXA DO CONTEUDO: o custo e (larg+7)/8 * alt bytes. Tela cheia
sao 1024 bytes sempre, mesmo que 90% seja preto. O proprio Studio recorta — o Export
do marca veio 104x50 em (12,7), nao 128x64 em (0,0). Recortar aqui e so nao jogar
fora o que a ferramenta ja fazia.
"""
from PIL import Image
import sys, os, re

L_TELA = 128            # largura do OLED: nenhuma imagem pode passar dela


def codificar(caminho):
    """Devolve (x, y, larg, alt, bytes). x,y sao onde a imagem entra na tela de 128x64."""
    im = Image.open(caminho).convert('1')
    cx = im.getbbox()
    if cx is None:
        raise SystemExit(f'{caminho}: imagem vazia')
    x0, y0, x1, y1 = cx
    # LARGURA SEMPRE MULTIPLA DE 8, e nao e capricho: com largura multipla de 8 o
    # empacotamento por linha e o continuo produzem exatamente os mesmos bytes, e a
    # pergunta "como comeca a linha seguinte quando a anterior parou no meio do byte?"
    # deixa de existir. Custa no maximo 7 colunas de preto; compra a garantia de que o
    # encoder nao pode estar errado sobre isso. Eliminar a duvida vale mais que resolve-la.
    w = -(-(x1 - x0) // 8) * 8
    if x0 + w > L_TELA:
        x0 = max(0, L_TELA - w)
        w = min(w, L_TELA - x0)
    rec = im.crop((x0, y0, x0 + w, y1))
    w, h = rec.size
    px = rec.load()
    dados, b, n = [], 0, 0
    for y in range(h):
        for x in range(w):                     # varredura continua: nao ha fim de linha
            if px[x, y]:
                b |= 1 << (7 - n)              # MSB primeiro
            n += 1
            if n == 8:
                dados.append(b); b, n = 0, 0
    if n:
        dados.append(b)                        # ultimo byte incompleto, resto em zero
    esperado = -(-w * h // 8)
    assert len(dados) == esperado, f'{len(dados)} bytes, o compilador espera {esperado}'
    return x0, y0, w, h, dados


def declaracao(nome, w, h, dados, por_linha=13):
    corpo = [f'{w}, {h}']
    linha = []
    for i, b in enumerate(dados):
        linha.append(f'0x{b:02X}')
        if len(linha) == por_linha:
            corpo.append(', '.join(linha)); linha = []
    if linha:
        corpo.append(', '.join(linha))
    txt = f'const image {nome}[] = {{\n    {{' + ',\n     '.join(corpo) + '}\n};'
    return txt


# ------------------------------------------------------------------ conferencia
def provar(png, export):
    """O encoder so vale se reproduzir, byte a byte, o que o Studio exportou."""
    _, _, w, h, meus = codificar(png)
    s = open(export).read()
    m = re.search(r'\{\s*(\d+)\s*,\s*(\d+)\s*,(.*?)\}\s*\n?\s*\};', s, re.S)
    ew, eh = int(m.group(1)), int(m.group(2))
    seus = [int(x, 16) for x in re.findall(r'0x([0-9A-Fa-f]{2})', m.group(3))]
    print(f'  geometria: meu {w}x{h}  |  Studio {ew}x{eh}  '
          f'{"IGUAL" if (w, h) == (ew, eh) else "DIVERGE"}')
    print(f'  bytes    : meu {len(meus)}  |  Studio {len(seus)}')
    if meus == seus:
        if w % 8:
            print('  => IDENTICOS byte a byte, e com largura NAO multipla de 8: as duas'
                  '\n     formulas de empacotamento divergiriam aqui. Conferencia conclusiva.')
            return 0
        print(f'  => identicos byte a byte, MAS a largura {w} e multipla de 8 — nesse caso'
              '\n     o empacotamento por linha e o continuo dao o mesmo resultado. O caso'
              '\n     NAO separa as hipoteses: conferencia PARCIAL, nao prova.')
        return 0
    dif = [i for i, (a, b) in enumerate(zip(meus, seus)) if a != b]
    print(f'  => DIVERGEM em {len(dif)} bytes, o primeiro no indice {dif[0] if dif else "-"}')
    return 1


if __name__ == '__main__':
    if sys.argv[1:2] == ['--provar']:
        sys.exit(provar(sys.argv[2], sys.argv[3]))
    for p in sys.argv[1:]:
        n = re.sub(r'\W', '_', os.path.splitext(os.path.basename(p))[0]).upper()
        x, y, w, h, d = codificar(p)
        print(f'// {os.path.basename(p)}: {w}x{h} em ({x},{y}) = {len(d)} bytes')
        print(declaracao('IMG_' + n, w, h, d))
        print(f'// image_oled({x}, {y}, OLED_WHITE, FALSE, IMG_{n}[0]);\n')
