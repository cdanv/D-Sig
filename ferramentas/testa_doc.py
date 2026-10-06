#!/usr/bin/env python3
"""Confere os NUMEROS e os COMANDOS do README contra o codigo.

POR QUE ISTO EXISTE. Escrevendo o README para o publico eu afirmei que o D-Sig pede
"firmware 2.3.2 ou mais novo". Nao ha nada no projeto que diga isso — eu inventei um
numero porque a frase pedia um. Ninguem teria pego: documentacao nao compila.

Documentacao que mente e pior que documentacao que falta, porque a que falta manda a
pessoa ler o codigo e a que mente a manda confiar. O que este modulo faz e simples:
toda afirmacao VERIFICAVEL do README tem de ser achada no codigo. Se o teto de MODs cair
para 16, ou o combo do menu mudar, ou o portao ganhar uma verificacao, o README reprova
no portao em vez de envelhecer calado.

O QUE ELE NAO FAZ: nao julga prosa. "Serve para separar contextos do mesmo jogo" nao e
verificavel e nao esta aqui. Afirmacao sem fonte no codigo nao entra no README — essa e
a regra que este arquivo impoe, e o jeito de impor e deixar de fora o que nao se checa.

USO:  python3 testa_doc.py <README.md> <D-Sig.gpc> <index.html> [n_verificacoes] [raiz]
      sai 0 se tudo bate; 1 e lista o que divergiu.
      A RAIZ e onde os arquivos prometidos pelo README devem estar; sem ela, a pasta do
      proprio README. Passa-se explicitamente quando o README esta fora do repositorio —
      e e o que as sabotagens fazem.
"""
import os
import re
import sys


def carrega(p):
    return open(p, encoding='utf-8').read()


def numeros_tabela(md, rotulo):
    """Devolve o valor em negrito da linha de tabela cujo primeiro campo casa o rotulo."""
    for ln in md.split('\n'):
        if not ln.startswith('|'):
            continue
        cel = [c.strip() for c in ln.strip('|').split('|')]
        if len(cel) >= 2 and rotulo.lower() in cel[0].lower():
            m = re.search(r'\*\*(\d+)\*\*|(\d+)', cel[1])
            if m:
                return int(m.group(1) or m.group(2))
    return None


def confere(readme, gpc, app, n_verif=None, raiz=None):
    """(ok, lista de divergencias, lista do que foi conferido)"""
    md = carrega(readme)
    g = carrega(gpc)
    a = carrega(app)
    mal, bem = [], []

    def ver(nome, cond, dito, achado):
        if cond:
            bem.append(f'{nome}: {dito}')
        else:
            mal.append(f'{nome}: o README diz {dito!r}, o codigo diz {achado!r}')

    # --- 1. a versao ---------------------------------------------------------
    mv = re.search(r'DS_VERSAO\s*=\s*"(D-Sig [0-9.a-z]+)"', g)
    vcod = mv.group(1).replace('D-Sig ', '') if mv else None
    # o [0-9.]+ guloso comia o ponto final de "**Versão 1.0.12.**" e reprovava a si mesmo
    mr = re.search(r'\*\*Vers[aã]o ([0-9]+(?:\.[0-9]+)*)\.?\*\*', md)
    vdoc = mr.group(1) if mr else None
    ver('versao', vdoc is not None and vdoc == vcod, vdoc, vcod)

    # --- 2. o teto de MODs ---------------------------------------------------
    mm = re.search(r'define\s+MAX_INST\s*=\s*(\d+)', g)
    nm = re.search(r'\bvar NMOD\s*=\s*(\d+)', a)
    teto = int(mm.group(1)) if mm else None
    ver('MAX_INST == NMOD', mm and nm and int(mm.group(1)) == int(nm.group(1)),
        'o mesmo teto nos dois', f'script {mm and mm.group(1)} / app {nm and nm.group(1)}')
    dmods = numeros_tabela(md, 'MODs por script')
    ver('MODs por script', dmods == teto, dmods, teto)
    # o texto corrido tambem afirma o teto
    ver('o texto corrido repete o teto', f'São {teto} MODs por script' in md
        or f'**{teto}**' in md, f'{teto} MODs', teto)

    # --- 3. destinos por MOD -------------------------------------------------
    ndst = len(re.findall(r'\bF1_DST[1-4]\b|\bSet_F1_Dst([1-4])\b', g))
    dst_doc = numeros_tabela(md, 'Destinos por MOD')
    # a fonte da verdade e o app: ele monta dst[] com tamanho fixo
    mdst = re.findall(r"dst:\s*\[([^\]]*)\]", a)
    ndst_app = (len(mdst[0].split(',')) if mdst else None)
    ver('destinos por MOD', dst_doc is not None and dst_doc == ndst_app,
        dst_doc, ndst_app)

    # --- 4. dominios ---------------------------------------------------------
    ndom_app = len(re.findall(r"MODE_S([1-4])\b", a))
    dom_doc = numeros_tabela(md, 'Domínios')
    ver('dominios', dom_doc == 4 and ndom_app >= 4, dom_doc, 4)

    # --- 5. o tamanho dos nomes ----------------------------------------------
    mdm = re.search(r'\bvar MAXDOM\s*=\s*(\d+)', a)
    maxdom = int(mdm.group(1)) if mdm else None
    dom_n = numeros_tabela(md, 'Nome de dom')
    ver('nome de dominio', dom_n is not None and dom_n == maxdom, dom_n, maxdom)
    # o nome do jogo vai em duas const string de 10, cortado em slice(0,10)/slice(10,20)
    corte = re.search(r"slice\(10,\s*(\d+)\)", a)
    jogo_cod = int(corte.group(1)) if corte else None
    jogo_doc = numeros_tabela(md, 'Nome do jogo')
    ver('nome do jogo', jogo_doc is not None and jogo_doc == jogo_cod,
        jogo_doc, jogo_cod)

    # --- 6. a conta da EEPROM ------------------------------------------------
    # 60 para os MODs + 3 da permutacao + 1 do selo = 64. Se o teto mudar, a conta muda.
    mods_sp = teto * 3 if teto else None
    conta = re.search(r'\*\*64 de 64\s*\n?palavras\*\*\s*—\s*(\d+) para os (\d+) MODs,\s*(\d+) para a permuta[çc][aã]o,\s*(\d+) para o selo',
                      md.replace('\n', '\n'))
    if not conta:
        conta = re.search(r'(\d+)\s+para os\s+(\d+)\s+MODs,\s*(\d+)\s+para a permuta[çc][aã]o,\s*(\d+)\s+para o selo',
                          md.replace('\n', ' '))
    if conta:
        a1, a2, a3, a4 = (int(x) for x in conta.groups())
        ver('a conta da EEPROM', a1 == mods_sp and a2 == teto and a1 + a3 + a4 == 64,
            f'{a1}+{a3}+{a4} para {a2} MODs', f'{mods_sp}+3+1 para {teto} MODs')
    else:
        mal.append('a conta da EEPROM: nao achei a frase no README para conferir')

    # --- 7. os combos do controle --------------------------------------------
    # O README promete comandos. Promessa de comando se confere achando o comando.
    combos = [
        ('R1 + OPTIONS abre o menu',
         r'event_press\(PS5_OPTIONS\)', r'R1 \+ OPTIONS'),
        ('SHARE 1s grava', r'PS5_SHARE', r'`SHARE`'),
        ('X confirma', r'PS5_CROSS', r'`X`'),
    ]
    for nome, pat_cod, pat_doc in combos:
        if re.search(pat_doc, md):
            ver(nome, re.search(pat_cod, g) is not None, 'o comando existe',
                'nao achei no script')

    # a tabela de troca de dominio: L3/R3, duplo-clique e segurar
    if 'duplo-clique no **L3**' in md:
        ver('troca de dominio pelos analogicos',
            re.search(r'PS5_L3', g) and re.search(r'PS5_R3', g)
            and re.search(r'PS5_L1', g) and re.search(r'PS5_R1', g),
            'L1/L3 e R1/R3 no script', 'falta um deles')

    # --- 8. o numero de verificacoes do portao -------------------------------
    nv_doc = re.search(r'port[aã]o de \*\*(\d+) verifica', md)
    if nv_doc and n_verif is not None:
        ver('verificacoes do portao', int(nv_doc.group(1)) == n_verif,
            nv_doc.group(1), n_verif)
    elif nv_doc:
        bem.append(f'verificacoes do portao: {nv_doc.group(1)} (nao conferido '
                   f'nesta chamada)')

    # --- 9. os arquivos que o README promete ---------------------------------
    # A RAIZ VEM DE FORA, nao do caminho do README. Deduzindo-a do README eu acoplei a
    # verificacao ao lugar do arquivo: um README em pasta temporaria — que e exatamente
    # o que a sabotagem usa — reprovava sozinho, por "index.html inexistente". As
    # sabotagens do firmware e do arquivo fantasma "reprovaram", mas pelo motivo errado,
    # e sabotagem que reprova pelo motivo errado nao provou nada.
    raiz = raiz or os.path.dirname(os.path.abspath(readme))
    for cam in re.findall(r'^\| `([^`]+)`', md, re.M):
        base = os.path.basename(cam)
        achou = os.path.exists(os.path.join(raiz, cam)) or \
            os.path.exists(os.path.join(raiz, base)) or \
            os.path.exists(os.path.join(raiz, '..', base))
        if not achou:
            mal.append(f'arquivo prometido no README e inexistente: {cam}')
        else:
            bem.append(f'arquivo {cam}: existe')

    # --- 10. nada de numero de firmware -------------------------------------
    # Foi exatamente o que eu inventei. Enquanto nao houver fonte, o README nao afirma.
    fw = re.search(r'firmware\s+v?\d+\.\d+', md, re.I)
    if fw:
        mal.append(f'o README afirma {fw.group(0)!r} e o projeto nao tem essa medida '
                   f'em lugar nenhum')
    else:
        bem.append('nenhum numero de firmware afirmado sem fonte')

    return (not mal), mal, bem


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(2)
    nv = int(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4] != '-' else None
    rz = sys.argv[5] if len(sys.argv) > 5 else None
    ok, mal, bem = confere(sys.argv[1], sys.argv[2], sys.argv[3], nv, rz)
    for b in bem:
        print(f'  ok  {b}')
    for m in mal:
        print(f'  XX  {m}')
    print(f'\n  => {len(bem)} afirmacoes do README conferidas contra o codigo'
          if ok else f'\n  => {len(mal)} afirmacoes do README divergem do codigo')
    sys.exit(0 if ok else 1)
