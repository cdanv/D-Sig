#!/usr/bin/env python3
"""Monta o repositorio no layout publico e PROVA que ele funciona de la.

    python3 ferramentas/empacotar.py [destino]

Roda dos dois layouts (ver ORIGEM, abaixo). Sem destino: ./repo na bancada de
desenvolvimento, ou <clone>-pacote/repo ao lado de um clone. O destino e APAGADO e
refeito; o zip sai na pasta de cima dele.

Nao basta copiar arquivos no lugar certo. O que faz esta ferramenta valer e a ultima
etapa: ela entra na copia e roda `python3 ferramentas/embutir.py` — o comando que o
README promete — e reprova se ele nao publicar o mesmo SHA-256 de origem. Pacote que
nunca foi executado da propria pasta e pacote que ninguem testou.

O QUE FICA DE FORA, e por que:
  biblioteca.json   os 4 jogos reais do Daniel. E configuracao pessoal dele, nao do
                    projeto, e o GitHub Pages serve tudo o que esta no repositorio como
                    arquivo publicamente legivel.
  sim_cfg.json      ENTRA, e agora e SINTETICO: sai do gera_molde.py, que declara 34
                    itens de cobertura e reprova se perder um. Era o Mad Max da biblioteca
                    do Daniel — configuracao pessoal, e com cobertura que era coincidencia
                    do que aquele jogo precisava. Sem molde o portao nao roda, e a
                    documentacao prometeria um comando impossivel.
  gera_molde.py     ENTRA. Sem ele o molde e um blob: a verificacao 17 regenera e compara,
                    para molde editado a mao nao perder a cobertura em silencio.
  *.bak, pacote/, __pycache__, os p*.py    historico de trabalho, nao projeto.

Os scripts de remendo (p1..p25) ficam de fora de proposito: cada um foi escrito para um
estado do arquivo que nao existe mais. Rodar um deles hoje nao conserta nada e pode
quebrar algo. O que sobrevive deles e a explicacao, e essa esta no LEIAME.
"""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import zipfile

AQUI = os.path.dirname(os.path.abspath(__file__))

# DE ONDE COPIAR. Dois layouts, o mesmo teste do embutir.py: a pasta de cima tem o
# index.html? Entao isto e um clone do repositorio publico e cada coisa ja esta no lugar
# em que vai ficar. Senao e a bancada de desenvolvimento, plana, com sim/ e oled/ ao lado.
#
#   desenvolvimento                  publico (um clone do GitHub)
#   dsig/                            D-Sig/              <- ORIGEM (raiz e icones)
#     index.html, D-Sig.gpc ...        index.html ...
#     pacote/icone-*.png               icone-*.png
#     empacotar.py      <- AQUI        ferramentas/      <- AQUI
#   sim/                                 sim/
#   oled/                                oled/
#
# Antes disto so o layout de desenvolvimento existia aqui, e num clone o empacotador
# reprovava antes de comecar, com 19 "arquivos prometidos e ausentes" — o pacote nao
# podia ser refeito a partir do proprio repositorio que ele gera.
_acima = os.path.dirname(AQUI)
PUBLICO = os.path.isfile(os.path.join(_acima, 'index.html'))
if PUBLICO:
    ORIGEM = _acima
    ICONES = _acima
    SIM = os.path.join(AQUI, 'sim')
    OLED = os.path.join(AQUI, 'oled')
else:
    ORIGEM = AQUI
    ICONES = os.path.join(AQUI, 'pacote')
    SIM = os.path.join(_acima, 'sim')
    OLED = os.path.join(_acima, 'oled')

# O SIMULADOR. Sete arquivos — o resto da pasta ../sim e rascunho de meses (binarios,
# .gcov, dezenas de .gpc intermediarios) e nao e projeto.
#
# ELE TEM DE IR NO PACOTE. O portao nao roda sem ele, e o README promete que
# `python3 ferramentas/embutir.py` funciona. A primeira versao deste empacotador deixou o
# simulador de fora e o pacote reprovou na propria prova, com "nao achei o simulador" —
# que e exatamente o erro que o usuario receberia ao clonar o repositorio. Pacote que
# nunca foi executado da propria pasta e pacote que ninguem testou.
SIMFILES = ['gpc2c.py', 'gpcrt.h', 'harness.c', 'fuzz.c', 'tri.c', 'zeta.c', 'mig.c']

RAIZ = [
    'index.html', 'D-Sig.gpc', 'manifest.json', 'sw.js',
    'README.md', 'LEIAME.md', 'LICENSE',
]
ICO = ['icone-192.png', 'icone-512.png', 'icone-maskable.png']
BANCADA = [
    'D-Sig.fonte.gpc',
    'embutir.py', 'limpar.py', 'empacotar.py', 'verificar_gpc.py',
    'testa_sim.py', 'testa_tabelas.py', 'testa_doc.py',
    'testa_a11y.js', 'testa_dom.js', 'tira_foto.js',
    'decodifica.py', 'testa_importa.js',
    'sim_gera.js', 'gera_molde.py', 'sim_cfg.json', 'sim_cfg_vazio.json',
    'publicado.json', 'sim_hash.json',
]
FORA = ['biblioteca.json']   # declarado para o relatorio, nao copiado


def sha(p):
    return hashlib.sha256(open(p, 'rb').read()).hexdigest()


def monta(dest):
    os.makedirs(os.path.join(dest, 'ferramentas', 'oled'), exist_ok=True)
    os.makedirs(os.path.join(dest, 'ferramentas', 'sim'), exist_ok=True)
    faltou = []
    for f in SIMFILES:
        o = os.path.join(SIM, f)
        if os.path.isfile(o):
            shutil.copy2(o, os.path.join(dest, 'ferramentas', 'sim', f))
        else:
            faltou.append(f'sim/{f}')
    for f in RAIZ:
        o = os.path.join(ORIGEM, f)
        if os.path.isfile(o):
            shutil.copy2(o, os.path.join(dest, f))
        else:
            faltou.append(f)
    for f in ICO:
        o = os.path.join(ICONES, f)
        if os.path.isfile(o):
            shutil.copy2(o, os.path.join(dest, f))
        else:
            faltou.append(f'pacote/{f}')
    for f in BANCADA:
        o = os.path.join(AQUI, f)
        if os.path.isfile(o):
            shutil.copy2(o, os.path.join(dest, 'ferramentas', f))
        else:
            faltou.append(f)
    for f in ('padrao.py', 'png2gpc.py'):
        o = os.path.join(OLED, f)
        if os.path.isfile(o):
            shutil.copy2(o, os.path.join(dest, 'ferramentas', 'oled', f))
        else:
            faltou.append(f'oled/{f}')
    return faltou


def main():
    # Sem argumento: no desenvolvimento, ./repo como sempre. Num clone, FORA dele — dentro
    # seria uma copia do repositorio no meio do repositorio, e o git a veria.
    if len(sys.argv) > 1:
        dest = sys.argv[1]
    elif PUBLICO:
        dest = os.path.join(os.path.dirname(ORIGEM), os.path.basename(ORIGEM) + '-pacote', 'repo')
    else:
        dest = os.path.join(AQUI, 'repo')
    dest = os.path.abspath(dest)
    # O destino e APAGADO antes de montar. Destino que e ou contem uma pasta de onde se
    # copia (`.`, `..`, `ferramentas`, a pasta de cima) apagaria o proprio projeto antes
    # da primeira copia. Recusado antes de qualquer rmtree. Destino DENTRO da origem e
    # permitido: e o ./repo de sempre no desenvolvimento.
    for o in (ORIGEM, AQUI, SIM, OLED, ICONES):
        o = os.path.abspath(o)
        if os.path.commonpath([dest, o]) == dest:
            print(f'  ERRO: apagar o destino {dest} apagaria {o}, de onde o pacote e copiado.')
            print('        Escolha uma pasta que nao contenha o projeto.')
            return 1
    if os.path.isdir(dest):
        shutil.rmtree(dest)
    print(f'  layout : {"publico (clone do repositorio)" if PUBLICO else "desenvolvimento"}')
    print(f'  destino: {dest}')
    faltou = monta(dest)
    if faltou:
        print('  ERRO: arquivos prometidos e ausentes -> ' + ', '.join(faltou))
        return 1
    for f in FORA:
        assert not os.path.exists(os.path.join(dest, f)), f
        assert not os.path.exists(os.path.join(dest, 'ferramentas', f)), f
    print(f'  copiados: {len(RAIZ)+len(ICO)} na raiz, '
          f'{len(BANCADA)} em ferramentas/, {len(SIMFILES)} em ferramentas/sim/, '
          f'2 em ferramentas/oled/')
    print(f'  de fora : {", ".join(FORA)}  (configuracao pessoal)')

    # --- A PROVA: o comando do README roda, de dentro do pacote --------------
    antes = sha(os.path.join(ORIGEM, 'D-Sig.gpc'))
    print('\n  --- rodando `python3 ferramentas/embutir.py` DENTRO do pacote ---')
    r = subprocess.run([sys.executable, os.path.join('ferramentas', 'embutir.py')],
                       cwd=dest, capture_output=True, text=True, timeout=2400)
    saida = (r.stdout or '') + (r.stderr or '')
    for ln in saida.strip().split('\n')[-4:]:
        print('  | ' + ln)
    if r.returncode != 0:
        print('  ERRO: o comando que o README promete NAO roda no layout publicado')
        return 1
    depois = sha(os.path.join(dest, 'D-Sig.gpc'))
    if antes != depois:
        print(f'  ERRO: o pacote publicou outro conteudo\n'
              f'        origem {antes[:16]} / pacote {depois[:16]}')
        return 1
    print(f'  ok: publicou o mesmo SHA-256 ({depois[:16]}...)')

    # --- faxina: a propria prova deixa lixo ---------------------------------
    # Rodar o embutir.py de dentro da copia gera __pycache__ em ferramentas/. Sem esta
    # faxina o zip carregava .pyc da minha maquina para o repositorio de quem clonar.
    for raiz, dirs, _ in os.walk(dest):
        for d in list(dirs):
            if d == '__pycache__':
                shutil.rmtree(os.path.join(raiz, d))
                dirs.remove(d)
    open(os.path.join(dest, '.gitignore'), 'w').write(
        '__pycache__/\n*.pyc\n'
        '# compilados do simulador: o portao os gera em pasta temporaria, mas um\n'
        '# experimento rodado a mao na bancada deixa o executavel aqui.\n'
        '*.o\n*.bin\n*.gcov\n*.gcno\n*.gcda\n'
        '# a biblioteca de jogos e pessoal: ela nao entra no repositorio.\n'
        'biblioteca.json\n')
    print('  faxina: __pycache__ removido; .gitignore escrito')

    # --- o zip --------------------------------------------------------------
    ver = json.load(open(os.path.join(dest, 'ferramentas', 'publicado.json')))['versao']
    tag = ver.replace('D-Sig ', '').replace(' ', '')
    zp = os.path.join(os.path.dirname(dest), f'D-Sig-{tag}-repo.zip')
    with zipfile.ZipFile(zp, 'w', zipfile.ZIP_DEFLATED) as z:
        for raiz, _, arqs in os.walk(dest):
            for a in sorted(arqs):
                p = os.path.join(raiz, a)
                z.write(p, os.path.relpath(p, dest))
    print(f'\n  zip: {zp}  ({os.path.getsize(zp)//1024} KB)')
    print('\n  SHA-256 do que vai ao ar:')
    for f in ['index.html', 'D-Sig.gpc', 'sw.js', 'manifest.json']:
        print(f'    {sha(os.path.join(dest, f))}  {f}')
    return 0


if __name__ == '__main__':
    sys.exit(main())
