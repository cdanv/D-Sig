#!/usr/bin/env python3
"""O PORTAO DE COMPORTAMENTO. Roda o script no simulador antes de publicar.

POR QUE ISSO EXISTE: o embutir.py audita ESTRUTURA — bytes identicos, nenhum comentario,
ancoras de pe, init limpo, arte fora das faixas de texto. Nada disso executa o script. O
simulador em ../sim (transpilador GPC->C, runtime, harness, fuzzer) existia desde 23/09 e
PAROU DE COMPILAR no dia em que o const image entrou no script — e ninguem percebeu,
porque nenhuma etapa o chamava. Tres versoes foram publicadas sobre uma rede desligada.

O QUE ELE GARANTE, falhando em vez de deixar publicar:
  1. o .gpc avulso transpila, compila e sobrevive a 60.000 voltas de fuzz;
  2. o script GERADO PELO APP, a partir do template que esta sendo publicado, idem;
  3. o TURBO do MOD_11 do molde sai 150/50/150/50/150/50/250 ms — os mesmos numeros
     que o PLOT do Device Monitor mediu no hardware (149,8/50,1 ms);
  4. o DELETAR? da lista exige 1000 ms de TRIANGLE, nem mais nem menos.

O 3 e o 4 sao os unicos numeros deste projeto que foram medidos em hardware E em
software e deram igual. Sao eles que ancoram o resto.

O HASH DO FUZZ nao e portao, e tripwire: ele muda em qualquer alteracao de comportamento,
intencional ou nao, e cabe a quem publica olhar e reconhecer. Fica registrado em
sim_hash.json por versao.

uso: python3 testa_sim.py <script.gpc> <index.html> [versao]
     e devolve 0 se tudo passou, 1 se algo reprovou.
"""
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile

def _acha_sim():
    """O simulador fica em ./sim no repositorio e em ../sim na bancada. Procurar nos dois
    e dizer onde achou e mais honesto que fixar um caminho e quebrar no outro."""
    _aqui = os.path.dirname(os.path.abspath(__file__))
    for _c in ('sim', os.path.join('..', 'sim')):
        _p = os.path.abspath(os.path.join(_aqui, _c))
        if os.path.isfile(os.path.join(_p, 'gpc2c.py')):
            return _p
    raise SystemExit('  ERRO: nao achei o simulador (gpc2c.py) em ./sim nem em ../sim')


SIM = _acha_sim()
AQUI = os.path.dirname(os.path.abspath(__file__))
REG = os.path.join(AQUI, 'sim_hash.json')
CFG = os.path.join(AQUI, 'sim_cfg.json')
# OS DOIS MOLDES, e por que sao dois.
#
# O sim_cfg.json e SINTETICO: sai do gera_molde.py, que declara 34 itens de cobertura e
# reprova se perder um. Ele usa ZETA, FIN e BLOK ao mesmo tempo, entao NUNCA produz funcao
# orfa — logo nao consegue reprovar na verificacao de funcao orfa, e molde que nao consegue
# reprovar nao prova nada. Por isso o molde VAZIO existe: ELE e o que reprova ali.
#
# (Era o Mad Max da biblioteca do Daniel. Trocar revelou tres defeitos nos testes; esta
#  no LEIAME, em "O molde do portao virou sintetico".)
CFG_VAZIO = os.path.join(AQUI, 'sim_cfg_vazio.json')
GERA = os.path.join(AQUI, 'sim_gera.js')
DOM = os.path.join(AQUI, 'testa_dom.js')
TAB = os.path.join(AQUI, 'testa_tabelas.py')
A11Y = os.path.join(AQUI, 'testa_a11y.js')

# O MOD_11 do molde: 2CLK no CROSS dispara TURBO no CROSS com tmp=[4,4,4,5]
# (150,150,150,250 ms) e lat=5 (50 ms). CROSS e o indice 6 no gpcrt.h.
# O gera_molde.py declara esse MOD como INTOCAVEL: e o unico numero do projeto medido no
# aparelho, e mexer nele cega a ponte entre o simulador e o Cronus.
CROSS = 6
TURBO_ESPERADO = [150, 50, 150, 50, 150, 50, 250]
TRI_ESPERADO = 1000

# O slot que o teste do ZETA deleta. O MOD_05 do molde fica no meio, carrega EXCL e ASSOC
# proprios, e tem MODs com relacao acima e abaixo dele — o gera_molde.py garante isso em
# "ZETA antes do slot 5" e "ZETA depois do slot 5". Deletar um slot sem relacao nenhuma
# nao remaneja nada e aprova vazio.
ZETA_SLOT = 5

# Mover o MOD do slot 3 para o 9 com L2+BAIXO: atravessa a faixa 3..9, onde o molde
# concentra relacoes de proposito ("ZETA na faixa 3..9"), entao mexe em varios slots de
# uma vez em vez de passear por cima de slots vazios.
ZETA_TROCA = (3, 9)

# A CHAVE DO BUG CONHECIDO. Enquanto False, o teste do ZETA DEVE reprovar: ele documenta
# um defeito real e nao pode barrar a publicacao da 1.0f, que ja esta no ar com ele.
# Quando o conserto entrar (1.0g), isto vira True e o teste passa a ser barreira dura.
#
# Se ele passar com a chave em False, alguma coisa consertou o bug sem ninguem pedir, e
# isso tambem e noticia — o portao avisa alto e nao barra.
ZETA_CONSERTADO = True

falhas = []
notas = []


def passo(nome, ok, detalhe=''):
    notas.append((nome, ok, detalhe))
    if not ok:
        falhas.append(nome)
    print(f'  [{"ok " if ok else "FALHOU"}] {nome}' + (f'   {detalhe}' if detalhe else ''))
    return ok


def passo_xfail(nome, ok, detalhe=''):
    """Teste de bug conhecido: hoje DEVE reprovar, e reprovar nao barra."""
    notas.append((nome, True, detalhe))
    if ok:
        print(f'  [!!!!!!] {nome}: PASSOU, e nao deveria.')
        print(f'          O bug conhecido parece consertado. Confirme e vire '
              f'ZETA_CONSERTADO=True.')
    else:
        print(f'  [xfail] {nome}   {detalhe}')
        print(f'          reprovou como esperado — e o bug conhecido do ZETA, '
              f'documentado no LEIAME.')
    return ok


def acha_node(pacote):
    """Procura um node_modules que contenha o pacote. Em vez de depender implicitamente
    de um diretorio alheio — que foi como o simulador ficou orfao — o portao procura,
    declara onde achou, e diz o nome do que falta.

    O jsdom e o playwright podem morar em lugares DIFERENTES: foi o que fez a conferencia
    de acessibilidade ser 'pulada' em silencio na primeira vez. Os dois caminhos entram
    no NODE_PATH."""
    cands = [AQUI, os.path.join(AQUI, '..', 'teste'), os.path.join(AQUI, '..')]
    g = _npm_global()
    if g:
        cands.append(os.path.dirname(g))
    for base in cands:
        nm = os.path.abspath(os.path.join(base, 'node_modules'))
        if os.path.isdir(os.path.join(nm, pacote)):
            return nm
    return None


_NPMG = []


def _npm_global():
    """Onde o npm instala pacotes globais. Perguntado a ele, nao adivinhado por HOME —
    o HOME deste processo pode nao ser o de quem instalou."""
    if _NPMG:
        return _NPMG[0]
    try:
        r = subprocess.run(['npm', 'root', '-g'], capture_output=True, text=True, timeout=30)
        p = r.stdout.strip()
        _NPMG.append(p if r.returncode == 0 and os.path.isdir(p) else None)
    except Exception:
        _NPMG.append(None)
    return _NPMG[0]


JSDOM = acha_node('jsdom')
PLAYW = acha_node('playwright')
NODEP = os.pathsep.join([p for p in (JSDOM, PLAYW) if p])


def roda(cmd, entrada=None, cwd=None, limite=180):
    env = dict(os.environ)
    if NODEP:
        env['NODE_PATH'] = NODEP
    try:
        return subprocess.run(cmd, input=entrada, capture_output=True, text=True,
                              cwd=cwd or SIM, timeout=limite, env=env)
    except subprocess.TimeoutExpired:
        return subprocess.CompletedProcess(cmd, 124, '', f'TIMEOUT apos {limite}s')


def constroi(gpc, nome, tmp):
    """Transpila e compila os tres executaveis. Devolve (ok, detalhe)."""
    c = os.path.join(tmp, nome + '.c')
    r = roda([sys.executable, os.path.join(SIM, 'gpc2c.py'), gpc, c])
    if r.returncode != 0:
        return False, 'transpilar: ' + (r.stderr.strip().split('\n')[-1] if r.stderr else '?')
    exes = {}
    for prog in ('harness', 'fuzz', 'tri', 'zeta', 'mig'):
        fonte = os.path.join(SIM, prog + '.c')
        if not os.path.exists(fonte):
            return False, f'{prog}.c nao existe em ../sim'
        exe = os.path.join(tmp, f'{nome}_{prog}')
        r = roda(['gcc', '-w', '-Werror=implicit-function-declaration',
                  '-O1', f'-I{SIM}', '-o', exe, fonte, c])
        if r.returncode != 0:
            return False, f'gcc {prog}: ' + (r.stderr.strip().split('\n')[0] if r.stderr else '?')
        exes[prog] = exe
    return True, exes


def mede_turbo(exe):
    """Duplo clique no CROSS e le as transicoes da saida. Devolve a lista de duracoes."""
    roteiro = '300 6 100\n350 6 0\n420 6 100\n470 6 0\nEND 3000\n'
    r = roda([exe, str(CROSS)], entrada=roteiro)
    if r.returncode != 0:
        return None, 'harness saiu ' + str(r.returncode)
    tr = []
    for lin in r.stdout.split('\n'):
        m = re.match(r'\s*(\d+)\s+out\d+=(-?\d+)', lin)
        if m:
            tr.append((int(m.group(1)), int(m.group(2))))
    # O TURBO comeca depois do segundo clique (t=420). Pega dali em diante.
    tr = [t for t in tr if t[0] >= 420]
    dur = [tr[i + 1][0] - tr[i][0] for i in range(len(tr) - 1)]
    return dur, ''


# ---------------------------------------------------------------------------
GPC = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(AQUI, 'D-Sig.gpc')
APP = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.join(AQUI, 'index.html')


def _versao_do_gpc(p):
    """A versao sai do PROPRIO script quando o embutir.py nao a passa.

    Era '?' nesse caso, e o '?' ia para o sim_hash.json como se fosse uma versao: ele
    virava o '_ultimo', e a rodada seguinte comparava 'inalterado desde a ?'. Uma rodada
    a mao apagava a linha de base do tripwire — o vigia perdia a memoria por ser
    consultado. O DS_VERSAO esta no arquivo que estamos testando; e so ler.
    """
    try:
        m = re.search(r'DS_VERSAO\s*=\s*"([^"]+)"', open(p, encoding='utf-8').read())
        if m:
            return m.group(1)
    except Exception:
        pass
    return '?'


VERSAO = sys.argv[3] if len(sys.argv) > 3 else _versao_do_gpc(GPC)

print(f'  simulador: {SIM}')
if JSDOM:
    print(f'  jsdom    : {JSDOM}')
    if PLAYW:
        print(f'  playwright: {PLAYW}')
else:
    passo('jsdom disponivel para rodar o app', False,
          'instale com: npm i jsdom  (em dsig/ ou em teste/)')
tmp = tempfile.mkdtemp(prefix='dsig_sim_')
hashes = {}
try:
    # --- 0. o MOLDE e o que o gerador diz que e ------------------------------
    # O sim_cfg.json nao e mais um jogo copiado da biblioteca: ele sai do gera_molde.py,
    # que declara 34 itens de cobertura e reprova se perder um. Essa garantia so vale se
    # o arquivo FOR a saida do gerador — um molde editado a mao mantem a aparencia e
    # perde a cobertura em silencio, que e o defeito do simulador dormindo outra vez.
    # Entao o portao regenera e compara.
    _gm = os.path.join(AQUI, 'gera_molde.py')
    if os.path.exists(_gm):
        _novo = os.path.join(tmp, 'molde.json')
        _rg = roda([sys.executable, _gm, _novo], cwd=AQUI, limite=120)
        if _rg.returncode != 0:
            passo('o molde do portao bate com o gera_molde.py', False,
                  (_rg.stdout or _rg.stderr or '').strip().split('\n')[-1][:120])
        else:
            _a = json.load(open(_novo, encoding='utf-8'))
            _b = json.load(open(CFG, encoding='utf-8'))
            _cob = [l for l in (_rg.stdout or '').split('\n') if 'cobertura' in l]
            passo('o molde do portao bate com o gera_molde.py', _a == _b,
                  (_cob[0].strip() if _a == _b and _cob else
                   'o sim_cfg.json divergiu do gerador: rode '
                   '`python3 gera_molde.py sim_cfg.json`'))

    # --- 1. o avulso ---------------------------------------------------------
    ok, res = constroi(GPC, 'avulso', tmp)
    if passo('avulso transpila e compila', ok, '' if ok else res):
        r = roda([res['fuzz'], '60000', '7'], limite=180)
        m = re.search(r'hash (\d+)', r.stderr or '')
        passo('avulso sobrevive a 60.000 voltas de fuzz',
              r.returncode == 0 and m is not None,
              f'hash {m.group(1)}' if m else (r.stderr or '')[:80])
        if m:
            hashes['avulso'] = m.group(1)

    # --- 2. o gerado pelo app, com O TEMPLATE QUE VAI SER PUBLICADO ----------
    # O index.html real ainda tem o template antigo neste ponto do embutir.py, entao
    # o teste monta uma copia com o template novo. Assim o que e testado e o que sai.
    app_tmp = os.path.join(tmp, 'index.html')
    fonte_app = open(APP, encoding='utf-8').read()
    mt = re.search(r'(<script type="text/plain" id="tpl">)(.*?)(</script>)', fonte_app, re.S)
    if not mt:
        passo('template localizado no index.html', False, 'ancora <script id="tpl"> ausente')
    else:
        novo = open(GPC, encoding='utf-8').read()
        open(app_tmp, 'w', encoding='utf-8').write(
            fonte_app[:mt.start(2)] + novo + fonte_app[mt.end(2):])
        r = roda(['node', GERA, app_tmp, CFG, os.path.join(tmp, 'cfg.gpc')], cwd=AQUI)
        if passo('o app gera script a partir deste template', r.returncode == 0,
                 (r.stdout or r.stderr or '').strip().split('\n')[-1][:90]):
            # --- a funcao orfa no GERADO, nao so no avulso -------------------
            # O embutir.py audita orfa no D-Sig.gpc. Mas o app substitui a Config_Zeta
            # INTEIRA, entao uma funcao ancorada no template pode ficar orfa no gerado —
            # e foi o que aconteceu: os Builds do Daniel deram 1, 1, 0 e 5 avisos
            # GPC3005 em quatro jogos, e o portao tinha deixado passar.
            _g = open(os.path.join(tmp, 'cfg.gpc'), encoding='utf-8').read()
            _orf = [_f for _f in re.findall(r'^function\s+(\w+)', _g, re.M)
                    if len(re.findall(r'\b' + _f + r'\s*\(', _g)) < 2]
            passo('o script gerado nao tem funcao orfa (GPC3005)',
                  not _orf, ', '.join(_orf) if _orf else 'nenhuma')

            # E o mesmo para um jogo SEM NENHUM MOD, onde o laco do Config_Zeta nao emite
            # nada e tudo o que pende dele fica orfao.
            _ov = os.path.join(tmp, 'vazio.gpc')
            _rv = roda(['node', GERA, app_tmp, CFG_VAZIO, _ov], cwd=AQUI)
            if _rv.returncode != 0:
                passo('o app gera script para jogo sem MOD', False,
                      (_rv.stdout or _rv.stderr or '').strip().split('\n')[-1][:80])
            else:
                _gv = open(_ov, encoding='utf-8').read()
                _ofv = [_f for _f in re.findall(r'^function\s+(\w+)', _gv, re.M)
                        if len(re.findall(r'\b' + _f + r'\s*\(', _gv)) < 2]
                passo('jogo sem MOD tambem nao tem funcao orfa',
                      not _ofv, ', '.join(_ofv) if _ofv else 'nenhuma')

            # --- os nomes de dominio, pelas DUAS vias do app ------------------
            # O codigo(j) e o scriptCompleto(j) sao duas vias para o mesmo dado, e e
            # onde a divergencia mora. Ja discordavam quando o recurso entrou.
            _rd = roda(['node', DOM, app_tmp, CFG], cwd=AQUI)
            passo('os nomes de dominio batem nas duas vias do app',
                  _rd.returncode == 0,
                  (_rd.stdout or _rd.stderr or '').strip().split('\n')[-1][:90])

            # --- as TABELAS, valor por valor ---------------------------------
            # O app grava um INDICE e o script traduz em milissegundos. Se as tabelas
            # discordarem, o app mostra "150ms", o Cronus aplica outra coisa, e NENHUM
            # teste de comportamento pega: o script faz o que a tabela DELE manda.
            _rt = roda([sys.executable, TAB, GPC, app_tmp], cwd=AQUI, limite=240)
            passo('as tabelas batem entre o app e o script',
                  _rt.returncode == 0,
                  (_rt.stdout or '').strip().split('\n')[-1].strip()[:100])

            # --- nome acessivel e alvo de toque, no navegador -----------------
            # O app e usado no celular com o controle na outra mao. Nome acessivel se
            # calcula na arvore, nao no fonte, entao isto roda no Chromium.
            _ch = None
            for _c in ('/opt/pw-browsers/chromium-1194/chrome-linux/chrome',
                       '/opt/pw-browsers/chromium/chrome-linux/chrome'):
                if os.path.exists(_c):
                    _ch = _c
                    break
            if _ch:
                os.environ['CHROMIUM'] = _ch
            _cfgv = CFG if os.path.exists(CFG) else CFG_VAZIO
            _ra = roda(['node', A11Y, app_tmp, _cfgv], cwd=AQUI, limite=240)
            _falta = (_ra.returncode != 0 and
                      ('playwright' in (_ra.stderr or '').lower() or not PLAYW))
            if _falta and os.environ.get('DSIG_SEM_A11Y') == '1':
                print('  [--  ] acessibilidade: pulada por DSIG_SEM_A11Y=1')
            elif _falta:
                passo('nome acessivel e alvo de toque no app', False,
                      'playwright ausente — instale com: npm i -g playwright, ou declare '
                      'DSIG_SEM_A11Y=1 para publicar sem esta conferencia')
            else:
                _linhas = [l for l in (_ra.stdout or '').split('\n') if 'FALHOU' in l]
                passo('nome acessivel e alvo de toque no app',
                      _ra.returncode == 0,
                      '; '.join(l.strip()[:60] for l in _linhas[:2]) if _linhas
                      else '8 conferencias em 4 telas')

            ok, res = constroi(os.path.join(tmp, 'cfg.gpc'), 'cfg', tmp)
            if passo('o gerado transpila e compila', ok, '' if ok else res):
                r = roda([res['fuzz'], '60000', '7'], limite=180)
                m = re.search(r'hash (\d+)', r.stderr or '')
                passo('o gerado sobrevive a 60.000 voltas de fuzz',
                      r.returncode == 0 and m is not None,
                      f'hash {m.group(1)}' if m else (r.stderr or '')[:80])
                if m:
                    hashes['configurado'] = m.group(1)

                # --- 3. o relogio, contra a medicao de hardware --------------
                dur, err = mede_turbo(res['harness'])
                if dur is None:
                    passo('TURBO do MOD_11 = 150/50/150/50/150/50/250 ms', False, err)
                else:
                    got = dur[:len(TURBO_ESPERADO)]
                    passo('TURBO do MOD_11 = 150/50/150/50/150/50/250 ms',
                          got == TURBO_ESPERADO, '/'.join(map(str, got)) + ' ms')

                # --- 4. o tempo de TRIANGLE para o DELETAR? ------------------
                r = roda([res['tri']])
                m = re.search(r'com (\d+) ms de TRIANGLE', r.stdout or '')
                passo(f'DELETAR? exige {TRI_ESPERADO} ms de TRIANGLE',
                      r.returncode == 0 and m is not None and int(m.group(1)) == TRI_ESPERADO,
                      (m.group(1) + ' ms') if m else (r.stdout or r.stderr or '').strip()[:80])

                # --- 5. o ZETA sobrevive ao desligamento? --------------------
                # Dois processos: a EEPROM (PVAR) atravessa num arquivo, as globais do
                # script morrem. E um ciclo de energia de verdade — chamar gpc_init()
                # duas vezes no mesmo processo nao simularia nada.
                eep = os.path.join(tmp, 'eeprom.bin')
                ra = roda([res['zeta'], 'A', str(ZETA_SLOT), eep])
                rb = roda([res['zeta'], 'B', eep]) if ra.returncode == 0 else None
                if ra.returncode != 0 or rb is None or rb.returncode != 0:
                    det = (ra.stderr or (rb.stderr if rb else '') or '').strip()[:90]
                    passo(f'o teste do ZETA roda (deleta o slot {ZETA_SLOT} e religa)',
                          False, det)
                else:
                    def mascaras(txt, rot):
                        d = {}
                        for lin in txt.split('\n'):
                            mm = re.match(rf'{rot} slot=(\d+) excl=(\d+) assoc=(\d+) bloq=(\d+)',
                                          lin)
                            if mm:
                                d[int(mm.group(1))] = tuple(int(mm.group(i)) for i in (2, 3, 4))
                        return d
                    dep = mascaras(ra.stdout, 'depois')
                    reb = mascaras(rb.stdout, 'reboot')
                    slots = sorted(set(dep) | set(reb))
                    ruins = [s for s in slots
                             if dep.get(s, (0, 0, 0)) != reb.get(s, (0, 0, 0))]
                    nome = f'o ZETA sobrevive a deletar o slot {ZETA_SLOT} e religar'
                    # GUARDA CONTRA APROVACAO VAZIA. "nenhum slot divergiu" e verdade
                    # tambem quando nenhum slot tem relacao: um molde sem ZETA passaria
                    # aqui sem exercitar uma linha da permutacao. O teste de reordenar ja
                    # tinha essa guarda (len(mexeu)>=2); este nao, e a diferenca so ficou
                    # visivel ao trocar de molde. Dez e o piso: o molde sintetico entrega
                    # 13 e o anterior entregava 12.
                    bastante = len(slots) >= 10
                    det = ('igual nos %d slots' % len(slots) if not ruins
                           else '%d de %d slots divergem: %s' % (len(ruins), len(slots),
                                                                 ','.join(map(str, ruins))))
                    if not bastante:
                        det += (' — SO %d slots com relacao: o molde nao exercita a '
                                'permutacao o bastante para este teste valer' % len(slots))
                    if ZETA_CONSERTADO:
                        passo(nome, (not ruins) and bastante, det)
                    else:
                        passo_xfail(nome, not ruins, det)

                # --- 6. e a REORDENACAO, que e o outro caminho que mexe em slot ---
                # Deletar e reordenar quebram o ZETA pelo mesmo motivo, mas por caminhos
                # diferentes no codigo (Compactar_Lista x Swap_Pos). Testar so um deixaria
                # metade do conserto sem prova.
                rc = roda([res['zeta'], 'C', str(ZETA_TROCA[0]), str(ZETA_TROCA[1]), eep])
                rd = roda([res['zeta'], 'B', eep]) if rc.returncode == 0 else None
                nome2 = 'o ZETA sobrevive a reordenar %d->%d e religar' % ZETA_TROCA
                if rc.returncode != 0 or rd is None or rd.returncode != 0:
                    passo(nome2, False,
                          (rc.stderr or (rd.stderr if rd else '') or '').strip()[:90])
                else:
                    an = mascaras(rc.stdout, 'antes')
                    dp = mascaras(rc.stdout, 'depois')
                    rb2 = mascaras(rd.stdout, 'reboot')
                    mexeu = [x for x in sorted(set(an) | set(dp))
                             if an.get(x, (0, 0, 0)) != dp.get(x, (0, 0, 0))]
                    sl2 = sorted(set(dp) | set(rb2))
                    ru2 = [x for x in sl2
                           if dp.get(x, (0, 0, 0)) != rb2.get(x, (0, 0, 0))]
                    # um teste que nao mexe em nada passaria sem provar nada
                    ok2 = (not ru2) and len(mexeu) >= 2
                    passo(nome2, ok2,
                          'a troca mexeu em %d slots; %s apos religar'
                          % (len(mexeu), 'nenhum diverge' if not ru2
                             else '%d divergem: %s' % (len(ru2), ru2)))

                # --- 7. a migracao a partir de uma EEPROM da 1.0f ------------
                # As SPVARs 61-63 guardavam o MOD 21 ate a 1.0f. Um Cronus que vem de la
                # chega com elas zeradas (MOD 21 nunca configurado — o caso do Daniel),
                # com configuracao de MOD, ou com lixo. O guarda tem de recusar nos tres.
                _migs = [('zeradas', ('0', '0', '0')),
                         ('com config de MOD', ('24803', '301', '1234567')),
                         ('com lixo', ('-1499591369', '-1499591369', '-1499591369'))]
                _mok, _mdet = True, []
                for _rot, _ws in _migs:
                    _rm = roda([res['mig'], eep] + list(_ws))
                    if _rm.returncode != 0:
                        _mok = False
                        _mdet.append(f'{_rot}: {(_rm.stdout or _rm.stderr or "").strip()[:40]}')
                passo('a EEPROM da 1.0f migra para a identidade nos 3 estados',
                      _mok, '; '.join(_mdet) if _mdet else 'zeradas, com config e com lixo')
finally:
    shutil.rmtree(tmp, ignore_errors=True)

# --- a DOCUMENTACAO contra o codigo -----------------------------------------
# Escrevendo o README para o publico eu afirmei "firmware 2.3.2 ou mais novo". Nao existe
# essa medida em lugar nenhum do projeto — eu inventei um numero porque a frase pedia um,
# e nada teria pego, porque documentacao nao compila. Aqui ela passa a compilar: toda
# afirmacao verificavel do README e procurada no codigo.
#
# Roda POR ULTIMO de proposito: uma das afirmacoes e quantas verificacoes o portao tem, e
# o portao so sabe isso quando acaba. len(notas)+1 conta esta mesma.
try:
    import testa_doc
    # A RAIZ e onde o README e os arquivos servidos moram: a pasta de cima quando a
    # bancada esta em ferramentas/, a propria quando o layout e plano. Mesmo teste que o
    # embutir.py usa. Procurar o README ao lado da bancada era o mesmo defeito de
    # caminho, e apareceu na primeira prova do pacote: "README.md nao existe".
    _acima = os.path.dirname(AQUI)
    _RAIZ = _acima if os.path.isfile(os.path.join(_acima, 'index.html')) else AQUI
    _rm = os.path.join(_RAIZ, 'README.md')
    if os.path.exists(_rm):
        _dok, _dmal, _dbem = testa_doc.confere(_rm, GPC, APP, len(notas) + 1, _RAIZ)
        passo('o README nao contradiz o codigo', _dok,
              f'{len(_dbem)} afirmacoes conferidas' if _dok else '; '.join(_dmal)[:160])
    else:
        passo('o README nao contradiz o codigo', False, 'README.md nao existe')
except Exception as _e:
    passo('o README nao contradiz o codigo', False, f'{type(_e).__name__}: {_e}')

# --- o tripwire -------------------------------------------------------------
if hashes and not falhas:
    reg = {}
    if os.path.exists(REG):
        try:
            reg = json.load(open(REG))
        except Exception:
            reg = {}
    ant = reg.get('_ultimo')
    antes = reg.get(ant, {}) if ant else {}
    for k, v in hashes.items():
        if antes.get(k) and antes[k] != v:
            print(f'  AVISO: o hash de comportamento ({k}) mudou de {antes[k]} para {v}')
            print(f'         vindo da {ant}. Se a mudanca era intencional, siga; se nao,')
            print(f'         alguma coisa alterou o comportamento sem voce pedir.')
        elif antes.get(k) == v:
            print(f'  hash {k}: inalterado desde a {ant}')
    reg[VERSAO] = hashes
    reg['_ultimo'] = VERSAO
    json.dump(reg, open(REG, 'w'), indent=2)

if falhas:
    print('  (hash nao registrado: so rodada aprovada vira linha de base)')
    print(f'  => PORTAO FECHADO: {len(falhas)} de {len(notas)} reprovaram -> ' + '; '.join(falhas))
    sys.exit(1)
print(f'  => portao aberto: {len(notas)} verificacoes de comportamento passaram')
