#!/usr/bin/env python3
"""Le um backup do Zen Studio (.znbk) e mostra as SPVARs de cada slot como MODs do D-Sig.

    python3 -I ferramentas/decodifica.py backup.znbk
    python3 -I ferramentas/decodifica.py backup.znbk --json          (saida para maquina)
    python3 -I ferramentas/decodifica.py backup.znbk --confere X.gpc (bate com o script?)

O .znbk e um ZIP: manifest.json diz qual script esta em cada slot, e slot-N/spvars.json
traz as 64 SPVARs DAQUELE slot, como [{"index": 0..63, "value": int32}] — index 0 e a
SPVAR_1. So esses dois arquivos sao lidos; bytecode, bvar e signature nao sao tocados.

O mapa de bits e o da SECAO 2 do D-Sig.fonte.gpc, e esta e a terceira copia dele: a
spvars() do app codifica, a deSpvars() do app decodifica, e esta decodifica de novo.
O portao (verificacao do importador, em testa_sim.py) prova que esta e a deSpvars()
concordam campo a campo em milhares de MODs — sem isso seriam duas leituras que podem
divergir caladas.

--confere compara as SPVARs dos MODs (1-60) com o Config_Inicial() de um script gerado
pelo app. Bater prova que o aparelho guardou exatamente o que o app mandou. A permutacao
(61-63) e o selo (64) sao do aparelho e ficam de fora: delete ou reordenacao feitos no
OLED mudam os MODs E a permutacao, e entao nao bater e o esperado.
"""
import json, re, sys, zipfile

NMOD = 20
FONTES = ['---', 'TOUCH_X', 'TOUCH_Y', 'LX', 'LY', 'RX', 'RY', 'L1', 'L2', 'L3', 'R1', 'R2',
          'R3', 'CROSS', 'CIRCLE', 'SQUARE', 'TRIANGLE', 'UP', 'DOWN', 'LEFT', 'RIGHT',
          'TOUCH', 'SHARE']
DESTINOS = ['---', 'L1', 'L2', 'L3', 'R1', 'R2', 'R3', 'CROSS', 'CIRCLE', 'SQUARE',
            'TRIANGLE', 'LX', 'LY', 'RX', 'RY', 'UP', 'DOWN', 'LEFT', 'RIGHT']
BOTOES = ['---', 'L1', 'L2', 'L3', 'R1', 'R2', 'R3', 'CROSS', 'CIRCLE', 'SQUARE',
          'TRIANGLE', 'UP', 'DOWN', 'LEFT', 'RIGHT', 'TOUCH', 'SHARE']
TIPOS = ['DIRECT', 'STATIC', 'TURBO']
DIRS = ['NEG', 'ABS', 'POS']
N_MULT, N_THR, N_HOLD = 19, 21, 63


class NaoEDSig(ValueError):
    pass


def _faixa(nome, x, lim):
    if not 0 <= x < lim:
        raise NaoEDSig(f'{nome}={x} fora de 0..{lim - 1}')
    return x


def mod(a, b, c):
    """Os 3 SPVARs de um slot -> dict com os MESMOS nomes de campo do app. None = vazio."""
    a, b, c = a & 0xFFFFFFFF, b & 0xFFFFFFFF, c & 0xFFFFFFFF
    if not a & 1:
        return None
    m = {f'd{i + 1}': (a >> (1 + i)) & 1 for i in range(4)}
    m['fonte'] = _faixa('FONTE', (a >> 5) & 31, len(FONTES))
    m['passivo'] = (a >> 10) & 1
    m['tipo'] = _faixa('DST_TIPO', (a >> 11) & 3, 3)
    v = _faixa('DESTINOS', (a >> 13) & 0x1FFFF, 19 ** 4)
    m['dst'] = [(v // 19 ** i) % 19 for i in range(4)]
    # pack de tempos do combo, repartido nos tres SPVARs (ver SECAO 2)
    pt = (((a >> 30) & 3) << 10) | (((b >> 29) & 7) << 7) | ((c >> 25) & 127)
    m['tmp'] = [(pt >> (3 * i)) & 7 for i in range(4)]
    v = _faixa('MULT*3+DIR', b & 63, N_MULT * 3)
    m['mult'], m['dir'] = divmod(v, 3)
    v = _faixa('THR', (b >> 6) & 511, N_THR * 20)
    m['tin'], m['tout'] = divmod(v, 20)
    m['gHoldM'] = (b >> 15) & 1
    m['gHoldT'] = _faixa('HOLD_TEMPO', (b >> 16) & 63, N_HOLD)
    m['delay'] = (b >> 22) & 3
    m['gAfterT'] = (b >> 24) & 7
    m['modo'] = (b >> 27) & 3
    m['gHold'] = _faixa('HOLD_BTN', c & 31, len(BOTOES))
    v = _faixa('TRIO', (c >> 5) & 0x1FFF, 17 ** 3)
    m['g2clk'], r = divmod(v, 17 * 17)
    m['gTog'], m['gAfter'] = divmod(r, 17)
    m['lat'] = (c >> 18) & 15
    m['ciclos'] = (c >> 22) & 7
    return m


def configurado(m):
    """A regra do nomeMod() do app: fonte, gatilho de estado ou destino."""
    return bool(m and (m['fonte'] or m['g2clk'] or m['gTog'] or m['gHold'] or m['gAfter']
                       or any(m['dst'])))


def ler(caminho):
    """-> [(indice do slot, nome do script, [64 int32] ou None, erro ou None)]

    Slot com problema volta com sv=None e o motivo: nunca derruba os outros e nunca some
    calado (a bateria de 10/11 achou os dois defeitos aqui e no app)."""
    try:
        z = zipfile.ZipFile(caminho)
    except (zipfile.BadZipFile, OSError) as e:
        raise SystemExit(f'{caminho}: nao e um arquivo .znbk (ZIP) valido ({e})')
    with z:
        try:
            man = json.loads(z.read('manifest.json'))
        except KeyError:
            raise SystemExit(f'{caminho}: o backup nao tem manifest.json')
        except ValueError:
            raise SystemExit(f'{caminho}: o manifest.json nao e JSON valido')
        saida, vistos = [], set()
        for s in man.get('slots', []):
            i = s.get('index') if isinstance(s, dict) else None
            if not isinstance(i, int) or i in vistos:
                continue
            vistos.add(i)
            nome = str(s.get('content_name') or f'slot {i + 1}')
            try:
                bruto = json.loads(z.read(f'slot-{i}/spvars.json'))
                sv = [0] * 64
                for x in bruto:
                    if 0 <= x['index'] < 64:
                        sv[x['index']] = int(x['value'])
            except KeyError:
                saida.append((i, nome, None, 'o backup nao tem as SPVARs deste slot'))
                continue
            except (ValueError, TypeError):
                saida.append((i, nome, None, 'as SPVARs deste slot estao ilegiveis'))
                continue
            # int32 com sinal, como o Cronus guarda: aceita tambem o valor sem sinal
            saida.append((i, nome, [((v + 2**31) % 2**32) - 2**31 for v in sv], None))
        return saida


def mods(sv):
    """-> ({slot 1..20: mod}, erro ou None)"""
    out, ruins = {}, []
    for k in range(NMOD):
        try:
            m = mod(*sv[3 * k:3 * k + 3])
        except NaoEDSig as e:
            ruins.append(f'slot {k + 1}: {e}')
            continue
        if configurado(m):
            out[k + 1] = m
    return out, ('; '.join(ruins) or None)


def resumo(m):
    p = []
    dom = ''.join(f'D{i}' for i in range(1, 5) if m[f'd{i}']) or 'nenhum dominio'
    p.append(dom)
    if m['fonte']:
        p.append(f'ALFA {FONTES[m["fonte"]]}' + (' PASSIVO' if m['passivo'] else ''))
    g = [(n, m[k]) for n, k in (('2CLK', 'g2clk'), ('TOG', 'gTog'), ('HOLD', 'gHold'),
                                ('AFTER', 'gAfter')) if m[k]]
    if g:
        p.append('GAMA ' + ', '.join(f'{n} {BOTOES[v]}' for n, v in g))
    d = [DESTINOS[x] for x in m['dst'] if x]
    if d:
        p.append(f'DELTA {TIPOS[m["tipo"]]} ' + '/'.join(d))
    return ' | '.join(p)


def config_inicial(gpc):
    """As 60 SPVARs que o Config_Inicial() de um script gerado escreve."""
    t = open(gpc, encoding='utf-8').read()
    i = t.find('function Config_Inicial() {')
    if i < 0:
        raise SystemExit(f'{gpc}: nao tem Config_Inicial()')
    corpo = t[i:t.find('\n}', i)]
    v = {}
    for l, n, x in re.findall(r'DS_([ABC])_(\d\d)\s*=\s*(-?\d+)', corpo):
        v[3 * (int(n) - 1) + 'ABC'.index(l)] = int(x)
    return [v.get(k, 0) for k in range(3 * NMOD)]


def main(av):
    if not av or av[0] in ('-h', '--help'):
        print(__doc__)
        return 0
    slots = ler(av[0])
    if '--json' in av:
        print(json.dumps([{'slot': i, 'script': n, 'spvars': sv,
                           'mods': mods(sv)[0] if sv else {},
                           'erro': ler_erro or (mods(sv)[1] if sv else None)}
                          for i, n, sv, ler_erro in slots], indent=1))
        return 0
    for i, n, sv, ler_erro in slots:
        print(f'slot {i + 1}: {n}')
        if ler_erro:
            print(f'   pulado: {ler_erro}')
            continue
        ms, erro = mods(sv)
        if erro:
            print(f'   nao e EEPROM do D-Sig ({erro})')
            continue
        if not ms:
            print('   nenhum MOD gravado' + ('' if any(sv) else ' (as 64 SPVARs estao zeradas)'))
            continue
        for k, m in ms.items():
            print(f'   MOD_{k:02d}  {resumo(m)}')
        print(f'   selo {(sv[63] >> 1) & 0x7FFFFFFF}   migrado {sv[63] & 1}')
    if '--confere' in av:
        alvo = config_inicial(av[av.index('--confere') + 1])
        iguais = [f'slot {i + 1}' for i, n, sv, _ in slots if sv and sv[:60] == alvo]
        print('\nconfere: ' + (', '.join(iguais) + ' = o Config_Inicial do script' if iguais
                               else 'NENHUM slot guarda o que o script manda'))
        return 0 if iguais else 1
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
