#!/usr/bin/env python3
"""ETAPA 4a da 1.0g — a fundacao: 21 MODs viram 20.

POR QUE: as SPVARs 61, 62 e 63 sao as do MOD 21. Elas precisam ficar livres para guardar
a PERMUTACAO que vai consertar o ZETA (etapa 4b). O MOD 21 e o preco, decidido com o
Daniel: 1 MOD em troca de delete e reordenacao no aparelho que sobrevivem ao desligamento.

POR QUE EM DUAS ETAPAS: esta aqui nao muda comportamento nenhum — so encurta escadas. Se
o portao reprovar depois dela, o defeito esta na poda, nao na logica nova. Fazer as duas
de uma vez misturaria as duas causas possiveis num unico diagnostico.

O QUE NAO SE TOCA, e por que cada um e um 21 que nao e slot:
  image_oled(21, 2, ...)   a coordenada x do timbre na tela de identidade
  FONTE_TOUCH = 21         o codigo da categoria de fonte, nao um numero de MOD
  SPVAR_21                 a terceira palavra do MOD 7
  "bits 16-21", "(0-21)"   comentarios sobre largura de campo

Rode com --conferir para ver o que seria feito sem escrever nada.
"""
import re
import sys

F = 'D-Sig.fonte.gpc'
CONFERIR = '--conferir' in sys.argv

PROTEGIDAS = ('image_oled(21, 2', 'FONTE_TOUCH', 'SPVAR_21,', 'SPVAR_21)')

s = open(F, encoding='utf-8').read()
orig = s
feitos = []


def e_comentario(lin):
    t = lin.lstrip()
    return t.startswith('//') or t.startswith('*') or t.startswith('/*')


def protegida(lin):
    return any(p in lin for p in PROTEGIDAS)


# --- 1. remover statements do slot 21 ----------------------------------------
# Cada padrao e uma FORMA de statement, nao uma linha: varias dessas aparecem tres por
# linha ("int Fin_19=0; int Fin_20=0; int Fin_21=0;"), e apagar a linha inteira levaria
# os slots 19 e 20 junto.
STATEMENTS = [
    (r' ?int \w+_21\s*=\s*0;',                      'declaracao do MOD 21'),
    (r'\s*if\(num == 21\) \{ Grava_Spv\(SPVAR_61,[^}]*\}',
     'gravacao do MOD 21 na EEPROM'),
    (r'\s*if\(n(?:um)? ?==? ?21\) [^;]*;',          'degrau 21 das escadas'),
    (r'\s*Ajust_Ref_Slot\(21, num\);',              'ajuste de referencia do slot 21'),
    (r'\s*Swap_Ref_Slot\(21, pa, pb\);',            'troca de referencia do slot 21'),
    (r'\s*Recalc_Um\(21\);',                        'recalculo do slot 21'),
    (r'\s*if\(Msk_\w+ & 1048576\) \w+\(21\);',      'bit 20 das mascaras (= MOD 21)'),
    (r'\s*DS_[ABC]_21 = get_pvar\(SPVAR_6[123],[^)]*\);', 'carga do MOD 21 da EEPROM'),
    (r'\s*if\(num <= 20 && Total_Inst > 20\) Compact_Pos\(20, 21\);',
     'degrau 21 da compactacao'),
    (r'\s*const string LBL_21 = "MOD_21";',         'rotulo do MOD 21'),
]

linhas = s.split('\n')
saida = []
for lin in linhas:
    if e_comentario(lin) or protegida(lin):
        saida.append(lin)
        continue
    nova = lin
    for pad, nome in STATEMENTS:
        nova, q = re.subn(pad, '', nova)
        if q:
            feitos.append((nome, q))
    if nova.strip() or not lin.strip():
        saida.append(nova.rstrip() if nova != lin else lin)
    # linha que ficou vazia de conteudo e descartada
s = '\n'.join(saida)

# --- 2. os limites ------------------------------------------------------------
LIMITES = [
    ('define MAX_INST          = 21;   // MODs no total — 21, todos na EEPROM',
     'define MAX_INST          = 20;   // MODs no total — 20, todos na EEPROM\n'
     '// v6: eram 21. As SPVARs 61-63, que guardavam o MOD 21, passaram a guardar a\n'
     '// PERMUTACAO — qual posicao original da tabela do app cada slot ocupa hoje. Sem ela\n'
     '// o Config_Zeta() reaplica a fiacao ZETA por posicao fixa a cada boot, e um delete\n'
     '// feito no aparelho sai errado no proximo religamento. Medido: 12 de 14 slots.'),
    ('define MAX_INST_EEP      = 21;   // MODs que a EEPROM comporta — 3 SPVARs cada, 63 de 64',
     'define MAX_INST_EEP      = 20;   // MODs que a EEPROM comporta — 3 SPVARs cada, 60 de 64'),
    ('    while(Esp_I <= 21) {\n        if(Get_Spvar_A(Esp_I) & 1) {',
     '    while(Esp_I <= 20) {\n        if(Get_Spvar_A(Esp_I) & 1) {'),
    ('    if(Boot_Inst <= 21) {', '    if(Boot_Inst <= 20) {'),
    ('    else if(Boot_Inst == 0)   Boot_Inst = 22;',
     '    else if(Boot_Inst == 0)   Boot_Inst = 21;'),
    ('    Work_E = (Work_E >> 1) & 0x1FFFFF;        // desce 1, limita a 21 bits (v3x: era 0x7FFF,',
     '    Work_E = (Work_E >> 1) & 0xFFFFF;         // desce 1, limita a 20 bits (v3x: era 0x7FFF,'),
    ('    Hp_Travado = 0x1FFFFF;   // 21 bits — no modo ATE isto significa "janela ja perdida"',
     '    Hp_Travado = 0xFFFFF;    // 20 bits — no modo ATE isto significa "janela ja perdida"'),
    ('    Fz_Travado = 0x1FFFFF;', '    Fz_Travado = 0xFFFFF;'),
    ('    Ent_Trava  = 0x1FFFFF;   // v3z1: nenhuma instancia opera ate passar por repouso',
     '    Ent_Trava  = 0xFFFFF;    // v3z1: nenhuma instancia opera ate passar por repouso'),
]
for velho, novo in LIMITES:
    assert velho in s, f'limite nao encontrado: {velho[:60]!r}'
    assert s.count(velho) == 1, f'limite ambiguo ({s.count(velho)}x): {velho[:60]!r}'
    s = s.replace(velho, novo, 1)
    feitos.append((f'limite: {velho.strip()[:52]}', 1))

# os dois while(Work_N <= 21) e o de Valor_Alvo_Assoc sobraram: trocam em bloco
n_w = s.count('while(Work_N <= 21)')
assert n_w == 2, f'esperava 2 while(Work_N <= 21), achei {n_w}'
s = s.replace('while(Work_N <= 21)', 'while(Work_N <= 20)')
feitos.append(('limite: while(Work_N <= 21) x2', 2))
n_e = s.count('while(Esp_I <= 21)')
assert n_e == 1, f'esperava 1 while(Esp_I <= 21) restante, achei {n_e}'
s = s.replace('while(Esp_I <= 21)', 'while(Esp_I <= 20)')
feitos.append(('limite: while(Esp_I <= 21) de Valor_Alvo_Assoc', 1))

# --- 3. o cabecalho, que ensina a arquitetura --------------------------------
CABECALHO = [
    ('*   21 MODs independentes. Cada um roteia um sinal de ENTRADA para ate 4 DESTINOS,',
     '*   20 MODs independentes. Cada um roteia um sinal de ENTRADA para ate 4 DESTINOS,'),
    ('*   96 bits persistentes por MOD = 3 SPVARs. 21 MODs x 3 = 63 das 64 SPVARs.',
     '*   96 bits persistentes por MOD = 3 SPVARs. 20 MODs x 3 = 60 das 64 SPVARs.\n'
     '*   As 4 que sobram: 61-63 guardam a PERMUTACAO (base-21, 7+7+6 digitos, mais um\n'
     '*   nibble de guarda nos bits 27-30 da 63) e a 64 guarda migracao + selo.'),
    ('*   que ninguem consegue zerar inteira. Um int tem 32 bits, e 21 MODs cabem em 21',
     '*   que ninguem consegue zerar inteira. Um int tem 32 bits, e 20 MODs cabem em 20'),
    ('*   E o que substitui o array que a linguagem nao tem. Com 21 itens a cadeia de ifs',
     '*   E o que substitui o array que a linguagem nao tem. Com 20 itens a cadeia de ifs'),
    ('*   virou ARVORE: 5 comparacoes em vez de 21.',
     '*   virou ARVORE: 5 comparacoes em vez de 20.'),
    ('*   (21 MODs ativos). Para comparar: a otimizacao da v7l tirou 61% do trabalho por',
     '*   (20 MODs ativos). Para comparar: a otimizacao da v7l tirou 61% do trabalho por'),
    ('int Boot_Inst = 0;   // 0 = nada pendente; 1-21 = proxima instancia a gravar;',
     'int Boot_Inst = 0;   // 0 = nada pendente; 1-20 = proxima instancia a gravar;'),
    ('int WzSlot               = 0;   // MOD em edicao (1-based: 1..MAX_INST)',
     'int WzSlot               = 0;   // MOD em edicao (1-based: 1..MAX_INST)'),
]
for velho, novo in CABECALHO:
    if velho == novo:
        continue
    assert velho in s, f'cabecalho nao encontrado: {velho[:60]!r}'
    s = s.replace(velho, novo, 1)
    feitos.append((f'cabecalho: {velho.strip()[:52]}', 1))

# --- relatorio ---------------------------------------------------------------
resumo = {}
for nome, q in feitos:
    resumo[nome] = resumo.get(nome, 0) + q
print(f'PARTE 15 (etapa 4a){"  — CONFERINDO, nada escrito" if CONFERIR else ""}')
for nome in sorted(resumo, key=lambda k: (-resumo[k], k)):
    print(f'  {resumo[nome]:4d}x  {nome}')
print(f'  linhas: {orig.count(chr(10))+1} -> {s.count(chr(10))+1}')

# nenhum rastro do slot 21 pode sobrar no codigo
sobra = []
for i, lin in enumerate(s.split('\n'), 1):
    if e_comentario(lin) or protegida(lin):
        continue
    corpo = lin.split('//')[0]
    if 'Boot_Inst = 21;' in corpo:
        continue                      # sentinela: 20 instancias gravadas, hora do selo
    if re.search(r'_21\b|\b21\b|0x1FFFFF|1048576', corpo):
        sobra.append((i, lin.strip()[:88]))
if sobra:
    print(f'  SOBROU rastro do slot 21 em {len(sobra)} linhas:')
    for i, lin in sobra:
        print(f'    {i:5d}  {lin}')
    sys.exit(1)
print('  nenhum rastro do slot 21 no codigo')

if not CONFERIR:
    open(F, 'w', encoding='utf-8').write(s)
    print(f'  {F} gravado')
