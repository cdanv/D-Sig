#!/usr/bin/env python3
"""Gera o MOLDE SINTETICO do portao — o `sim_cfg.json` que vai ao repositorio.

POR QUE SINTETICO. O molde era o Mad Max, tirado da biblioteca do Daniel. Funcionava,
mas trazia dois problemas para um repositorio publico: e configuracao pessoal dele, e —
pior — ninguem sabia POR QUE cada MOD daquele estava ali. Molde herdado de um jogo real
cobre o que aquele jogo precisava, nao o que o portao precisa verificar. A cobertura era
coincidencia.

Aqui cada MOD existe por um motivo escrito ao lado dele. O molde deixa de ser um dado
achado e passa a ser um dado PROJETADO: se amanha um campo novo entrar no layout de bits,
o lugar de cobri-lo e este arquivo, e a falta aparece na leitura.

O QUE O MOLDE TEM DE SUSTENTAR, porque o portao depende disso:

  MOD_11 = TURBO 150/50/150/50/150/50/250 ms no CROSS, disparado por 2CLK no CROSS.
           E o unico numero do projeto medido no PLOT do Device Monitor com o Cronus na
           mao (149,8/50,1 ms). Mexer nele cega a unica ponte entre o simulador e o
           aparelho — entao tmp=[4,4,4,5] e lat=5 sao INTOCAVEIS.
  ZETA     relacoes espalhadas por slots acima e abaixo do 5 (que o teste deleta) e
           atravessando a faixa 3..9 (que o teste reordena). Sem isso os dois testes
           passam sem mexer em nada, que e passar sem provar.
  SEM ORFA os tres Zeta_* e os Perm_* so existem se ALGUM MOD usar EXCL, ASSOC, BLOQ,
           FIN e BLOK. Molde que nao usa um deles produz GPC3005 e o portao acusa — e e
           de proposito que o `sim_cfg_vazio.json` continua existindo: ELE e o molde que
           CONSEGUE reprovar na verificacao de funcao orfa. Este aqui nunca reprovaria,
           e um teste que nao consegue reprovar nao prova nada.

COBERTURA DECLARADA. No fim o script CONTA o que cobriu e reprova se faltar alguma coisa
da lista. Molde que perde cobertura em silencio e o mesmo defeito do simulador dormindo.

USO:  python3 gera_molde.py [saida.json]
"""
import json
import sys

# --- as tabelas, pelos indices que o app grava --------------------------------
# FONTES  0 ---  1 TOUCH_X  2 TOUCH_Y  3 LX  4 LY  5 RX  6 RY  7 L1  8 L2  9 L3
#        10 R1 11 R2 12 R3 13 CROSS 14 CIRCLE 15 SQUARE 16 TRIANGLE
#        17 UP 18 DOWN 19 LEFT 20 RIGHT 21 TOUCH 22 SHARE
# DESTINOS 0 ---  1 L1  2 L2  3 L3  4 R1  5 R2  6 R3  7 CROSS  8 CIRCLE  9 SQUARE
#         10 TRIANGLE 11 LX 12 LY 13 RX 14 RY 15 UP 16 DOWN 17 LEFT 18 RIGHT
# BOTOES  0 ---  1 L1  2 L2  3 L3  4 R1  5 R2  6 R3  7 CROSS  8 CIRCLE  9 SQUARE
#        10 TRIANGLE 11 UP 12 DOWN 13 LEFT 14 RIGHT 15 TOUCH 16 SHARE
# TPASSO  0 30ms 1 50ms 2 70ms 3 100ms 4 150ms 5 250ms 6 500ms 7 1.0s
# TLAT    0 --- 1 10ms 2 20ms 3 30ms 4 40ms 5 50ms ... 15 750ms
# TAFTER  0 50ms 1 100ms 2 150ms 3 200ms 4 300ms 5 500ms 6 1.0s 7 2.0s
# TDELAY  0 OFF 1 300ms 2 700ms 3 1.2s
CROSS_D, CROSS_B = 7, 7

NMOD = 20


def mod(**kw):
    """Um MOD com os padroes do modVazio() do app, sobrescrito pelo que se declara."""
    m = {'nota': '', 'd1': 0, 'd2': 0, 'd3': 0, 'd4': 0, 'fonte': 0, 'passivo': 0,
         'mult': 9, 'tin': 1, 'tout': 0, 'dir': 1,
         'g2clk': 0, 'gTog': 0, 'gHold': 0, 'gHoldT': 25, 'gHoldM': 0,
         'gAfter': 0, 'gAfterT': 5,
         'tipo': 0, 'dst': [0, 0, 0, 0], 'tmp': [3, 3, 3, 3], 'lat': 4,
         'modo': 0, 'ciclos': 0, 'excl': [], 'assoc': [], 'bloq': [],
         'delay': 0, 'gBlok': 0,
         'fin2clk': 0, 'finTog': 0, 'finHold': 0, 'finAfter': 0}
    m.update(kw)
    return m


# Os alvos de ZETA sao indices 0-based (MOD_01 = 0), como o app grava.
MODS = [
    # 01 — ALFA de eixo + BETA completa (MULT, THR_IN, THR_OUT, DIR). E o MOD que faz
    #      o empacotamento a*R+b ser exercitado com os dois operandos longe do padrao;
    #      foi ali que a auditoria da 1.0.12 achou o THR_OUT transbordando.
    mod(d1=1, fonte=3, mult=14, tin=4, tout=16, dir=2, tipo=0, dst=[13, 0, 0, 0]),

    # 02 — ALFA de eixo em DOIS dominios, para o MOD existir em D1 e D2 ao mesmo tempo.
    mod(d1=1, d2=1, fonte=4, tipo=0, dst=[12, 0, 0, 0]),

    # 03 — alvo de ASSOC de varios, e o MOD que o teste de reordenar MOVE (3 -> 9).
    #      Tem de ter relacao propria, senao a troca nao mexe em mascara nenhuma.
    mod(d1=1, fonte=7, tipo=0, dst=[4, 0, 0, 0], assoc=[0, 1]),

    # 04 — STATIC sem ALFA, ligado por HOLD no modo APOS. Cobre gHold + gHoldM=0.
    mod(d1=1, tipo=1, dst=[5, 0, 0, 0], gHold=3, gHoldT=25, assoc=[0, 1], bloq=[2]),

    # 05 — O SLOT QUE O TESTE DELETA. Carrega EXCL e ASSOC para a delecao ter o que
    #      remanejar: se ele nao tivesse relacao, deletar nao provaria nada.
    mod(d1=1, tipo=2, dst=[2, 0, 0, 0], tmp=[7, 3, 3, 3], lat=7,
        gHold=3, gHoldT=40, excl=[2], assoc=[0, 1]),

    # 06 — HOLD no modo ATE (gHoldM=1), o caminho oposto do MOD_04, e TOUCH como botao
    #      de gatilho. Dois dominios.
    mod(d1=1, d2=1, tipo=2, dst=[8, 0, 0, 0], tmp=[4, 3, 3, 3], lat=0,
        gHold=15, gHoldT=18, gHoldM=1),

    # 07 — TOGGLE + HOLD coexistindo no mesmo MOD, com EXCL. Cobre dois GAMA simultaneos.
    mod(d1=1, d2=1, tipo=1, dst=[1, 0, 0, 0], gTog=1, gHold=15, gHoldT=30, excl=[3]),

    # 08 — ALFA de eixo COM gatilho, e FIN no TOGGLE: o gatilho que so DESLIGA. Sem um
    #      MOD assim a Zeta_Fin fica orfa e o Zen Studio avisa GPC3005.
    mod(d1=1, fonte=4, tipo=0, dst=[14, 0, 0, 0], gTog=1, finTog=1,
        excl=[3], assoc=[6]),

    # 09 — O SLOT DE DESTINO da reordenacao (3 -> 9). TURBO de 4 passos com tempos
    #      diferentes em cada um, disparado por 2CLK.
    mod(d1=1, tipo=2, dst=[9, 9, 9, 9], tmp=[3, 4, 5, 6], lat=4, g2clk=9, bloq=[2]),

    # 10 — TURBO com ciclos e modo, para os campos TURBO_MODO e TURBO_CICLOS saírem do
    #      zero. Eles tem 2 e 3 bits; zerados, a tabela deles nunca e conferida.
    mod(d1=1, tipo=2, dst=[10, 10, 10, 10], tmp=[2, 3, 2, 4], lat=4,
        modo=2, ciclos=3, assoc=[8]),

    # 11 — INTOCAVEL. 150/50/150/50/150/50/250 ms no CROSS, por 2CLK no CROSS. E o unico
    #      numero do projeto medido no aparelho (PLOT do Device Monitor: 149,8/50,1 ms).
    #      tmp=[4,4,4,5] = 150,150,150,250 e lat=5 = 50 entre os passos.
    mod(d1=1, tipo=2, dst=[CROSS_D] * 4, tmp=[4, 4, 4, 5], lat=5,
        g2clk=CROSS_B, bloq=[2]),

    # 12 — BLOQ em dois alvos de uma vez, no D2.
    mod(d2=1, fonte=4, tipo=0, dst=[5, 0, 0, 0], bloq=[12, 15]),

    # 13 — alvo de ASSOC vindo do D2, e ele mesmo com BLOQ. Cadeia de duas pontas.
    mod(d2=1, fonte=4, tipo=0, dst=[2, 0, 0, 0], bloq=[15]),

    # 14 — tres BLOQ, TOGGLE e HOLD juntos, e DELAY ligado. O DELAY tem 2 bits e so e
    #      exercitado por um MOD que o use.
    mod(d2=1, tipo=1, dst=[5, 0, 0, 0], gTog=10, gHold=5, gHoldT=12,
        delay=2, bloq=[10, 11, 15]),

    # 15 — DOIS destinos no mesmo MOD. O campo F1_DST guarda 4 destinos em base-19; com
    #      um destino so, os tres de cima nunca mudam de valor.
    mod(d2=1, fonte=5, tipo=0, dst=[11, 9, 0, 0], assoc=[12]),

    # 16 — TURBO de passo unico e constante, ligado por TOGGLE, no D2.
    mod(d2=1, tipo=2, dst=[CROSS_D] * 4, tmp=[7, 7, 7, 7], lat=0, gTog=3, assoc=[12]),

    # 17 — BLOK: o gatilho que SUSPENDE enquanto segurado. E o unico MOD que faz a
    #      Zeta_Blk existir; sem ele, GPC3005.
    mod(d2=1, tipo=1, dst=[5, 0, 0, 0], gHold=12, gHoldT=50, gBlok=4),

    # 18 — PASSIVO + AFTER + FIN no AFTER, no D3. O PASSIVO suprime a entrada E os botoes
    #      de GAMA (Suprime_Gatilhos), que foi o "o TRIANGLE nao funciona" da 1.0f.
    #      Tambem e o unico MOD do D3: sem ele o dominio 3 nunca liga no molde.
    mod(d3=1, fonte=16, passivo=1, tipo=0, dst=[10, 0, 0, 0],
        gAfter=16, gAfterT=4, finAfter=1),

    # 19 — ALFA de gatilho analogico (L2) com BETA de janela estreita e DIR invertida,
    #      no D3. Cobre catFonte de gatilho, que nao e eixo nem botao.
    mod(d3=1, fonte=8, mult=4, tin=2, tout=9, dir=0, tipo=0, dst=[6, 0, 0, 0]),

    # 20 — QUATRO destinos distintos, 2CLK com FIN, e o unico MOD do D4. O ultimo slot
    #      e tambem o que a auditoria da 1.0.12 pegou corrompendo a biblioteca pela seta
    #      de descer — o molde ocupar o slot 20 mantem esse limite sob o portao.
    mod(d4=1, fonte=1, tipo=0, dst=[15, 16, 17, 18], g2clk=11, fin2clk=1,
        assoc=[17]),
]

assert len(MODS) == NMOD, f'{len(MODS)} MODs, esperava {NMOD}'

JOGO = {
    'nome': 'MOLDE SINTETICO',          # 15 caracteres, cabe nos 20 do OLED
    # Os 4 dominios com nome, para o caminho do nome de dominio ser exercitado pelo
    # portao em vez de so pelo testa_dom.js. 9 caracteres e o limite (MAXDOM).
    'cores': [16, 10, 19, 13],
    'dom': ['A PE', 'VEICULO', 'MIRA', 'MENU'],
    'mods': MODS,
    'noZen': 0,
}

# --- a cobertura, declarada e conferida --------------------------------------
# Molde que perde cobertura em silencio e o mesmo defeito do simulador dormindo tres
# versoes: continua verde, e nao verifica mais o que dizia verificar.
EXIGE = {
    'EXCL':            lambda M: any(m['excl'] for m in M),
    'ASSOC':           lambda M: any(m['assoc'] for m in M),
    'BLOQ':            lambda M: any(m['bloq'] for m in M),
    'BLOK':            lambda M: any(m['gBlok'] for m in M),
    'FIN (algum)':     lambda M: any(m['fin2clk'] or m['finTog'] or m['finHold']
                                     or m['finAfter'] for m in M),
    'DIRECT':          lambda M: any(m['tipo'] == 0 and any(m['dst']) for m in M),
    'STATIC':          lambda M: any(m['tipo'] == 1 for m in M),
    'TURBO':           lambda M: any(m['tipo'] == 2 for m in M),
    '2CLK':            lambda M: any(m['g2clk'] for m in M),
    'TOGGLE':          lambda M: any(m['gTog'] for m in M),
    'HOLD modo APOS':  lambda M: any(m['gHold'] and not m['gHoldM'] for m in M),
    'HOLD modo ATE':   lambda M: any(m['gHold'] and m['gHoldM'] for m in M),
    'AFTER':           lambda M: any(m['gAfter'] for m in M),
    'DELAY ligado':    lambda M: any(m['delay'] for m in M),
    'PASSIVO':         lambda M: any(m['passivo'] for m in M),
    'TURBO_MODO':      lambda M: any(m['modo'] for m in M),
    'TURBO_CICLOS':    lambda M: any(m['ciclos'] for m in M),
    'BETA MULT != 9':  lambda M: any(m['mult'] != 9 for m in M),
    'BETA THR_OUT':    lambda M: any(m['tout'] for m in M),
    'BETA DIR != 1':   lambda M: any(m['dir'] != 1 for m in M),
    'fonte de eixo':   lambda M: any(m['fonte'] in (3, 4, 5, 6) for m in M),
    'fonte de gatilho': lambda M: any(m['fonte'] in (8, 11) for m in M),
    'fonte de touch':  lambda M: any(m['fonte'] in (1, 2, 21) for m in M),
    '2 destinos':      lambda M: any(sum(1 for d in m['dst'] if d) == 2 for m in M),
    '4 destinos':      lambda M: any(sum(1 for d in m['dst'] if d) == 4 for m in M),
    'D1': lambda M: any(m['d1'] for m in M),
    'D2': lambda M: any(m['d2'] for m in M),
    'D3': lambda M: any(m['d3'] for m in M),
    'D4': lambda M: any(m['d4'] for m in M),
    'slot 20 ocupado': lambda M: bool(M[19]['fonte'] or any(M[19]['dst'])),
    'TURBO medido intacto': lambda M: (M[10]['tipo'] == 2
                                       and M[10]['tmp'] == [4, 4, 4, 5]
                                       and M[10]['lat'] == 5
                                       and M[10]['g2clk'] == CROSS_B
                                       and M[10]['dst'] == [CROSS_D] * 4),
    # Os dois testes de ZETA precisam de relacao dos dois lados do slot 5 e dentro da
    # faixa 3..9. Sem isto eles passam sem mexer em mascara nenhuma.
    'ZETA antes do slot 5': lambda M: any(m['excl'] or m['assoc'] or m['bloq']
                                          for m in M[:4]),
    'ZETA depois do slot 5': lambda M: sum(1 for m in M[5:]
                                           if m['excl'] or m['assoc'] or m['bloq']) >= 8,
    'ZETA na faixa 3..9': lambda M: sum(1 for m in M[2:9]
                                        if m['excl'] or m['assoc'] or m['bloq']) >= 4,
}


def main():
    falta = [k for k, f in EXIGE.items() if not f(MODS)]
    print(f'  cobertura: {len(EXIGE) - len(falta)}/{len(EXIGE)}')
    if falta:
        print('  ERRO: o molde deixou de cobrir -> ' + ', '.join(falta))
        return 1
    vivos = sum(1 for m in MODS
                if m['fonte'] or any(m['dst'])
                or m['g2clk'] or m['gTog'] or m['gHold'] or m['gAfter'])
    rel = sum(len(m['excl']) + len(m['assoc']) + len(m['bloq']) for m in MODS)
    print(f'  {vivos} MODs vivos de {NMOD}; {rel} relacoes de ZETA')
    saida = sys.argv[1] if len(sys.argv) > 1 else 'sim_cfg.json'
    json.dump({'jogos': [JOGO], 'ordem': [0]}, open(saida, 'w', encoding='utf-8'),
              ensure_ascii=False, indent=1)
    print(f'  {saida} gravado')
    return 0


if __name__ == '__main__':
    sys.exit(main())
