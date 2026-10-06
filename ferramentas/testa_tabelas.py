#!/usr/bin/env python3
"""Confere TODA tabela que existe nos dois lados: app e script.

POR QUE ESTA E A AUDITORIA MAIS IMPORTANTE DO PROJETO: o app grava um INDICE nos bits, e o
script traduz esse indice em milissegundos. Se as duas tabelas discordarem, o app mostra
"150ms", o Cronus aplica outra coisa, nada dá erro e nada avisa. Nenhum teste de
comportamento pega: o script faz exatamente o que a tabela DELE manda.

Ja aconteceu neste projeto, em escala menor: o Football tinha tmp=250/50 ms no script e
150/30 ms na biblioteca, porque o script era mais novo que a exportacao.

O QUE SE CONFERE:
  - as tabelas de TEMPO, valor por valor: TPASSO, TLAT, TAFTER, TDELAY, THOLD;
  - as tabelas de ESCOLHA, pelo TAMANHO contra o radix do empacotamento: um indice fora
    do radix transborda para o campo vizinho, que foi o defeito do THR_OUT;
  - os limites do editor do OLED contra o que o app oferece.

uso: python3 testa_tabelas.py [script.gpc] [index.html]
"""
import json
import os
import re
import sys

AQUI = os.path.dirname(os.path.abspath(__file__))
GPC = os.path.abspath(sys.argv[1]) if len(sys.argv) > 1 else os.path.join(AQUI, 'D-Sig.gpc')
APP = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else os.path.join(AQUI, 'index.html')

g = open(GPC, encoding='utf-8').read()
h = open(APP, encoding='utf-8').read()
_m = re.search(r'<script type="text/plain" id="tpl">(.*?)</script>', h, re.S)
assert _m, 'template nao encontrado no index.html'
app = h[:_m.start(1)] + h[_m.end(1):]

falhas = []


def diz(nome, ok, det=''):
    if not ok:
        falhas.append(nome)
    print(f'  [{"ok " if ok else "FALHOU"}] {nome}' + (f'   {det}' if det else ''))


def tab_script(fn):
    """Le a escada de 'if(idx == N) return V;' de uma funcao e devolve a lista."""
    m = re.search(r'function ' + fn + r'\(\w+\)\s*\{(.*?)\n\}', g, re.S)
    if not m:
        return None
    corpo = m.group(1)
    vals = {int(a): int(b) for a, b in
            re.findall(r'if\(\w+\s*==\s*(\d+)\)\s*return\s*(-?\d+);', corpo)}
    mf = re.search(r'\n\s*return\s*(-?\d+);\s*$', corpo)
    if mf:
        vals[max(vals) + 1 if vals else 0] = int(mf.group(1))
    return [vals[k] for k in sorted(vals)] if vals else None


def tab_app(nome):
    m = re.search(r'var ' + nome + r'\s*=\s*\[(.*?)\];', app, re.S)
    if not m:
        return None
    return [x.strip().strip("'\"") for x in m.group(1).split(',')]


def ms(txt):
    """'0.15s' -> 150, '150ms' -> 150, 'OFF'/'---'/'ATIVO' -> None"""
    t = txt.strip()
    if re.match(r'^-?\d+(\.\d+)?s$', t):
        return int(round(float(t[:-1]) * 1000))
    if re.match(r'^\d+ms$', t):
        return int(t[:-2])
    if re.match(r'^\d+\.\d+s$', t):
        return int(round(float(t[:-1]) * 1000))
    return None


print('--- tabelas de TEMPO, valor por valor ---')
PARES = [
    ('TPASSO', 'Trb_Tempo_Ms',    'tempo de cada passo do TURBO'),
    ('TLAT',   'Trb_Lat_Ms',      'latencia entre passos do TURBO'),
    ('TAFTER', 'After_Ms',        'atraso do GAMA AFTER'),
    ('TDELAY', 'Delay_Ms',        'DELAY do MOD'),
]
for nome_app, fn, desc in PARES:
    a = tab_app(nome_app)
    b = tab_script(fn)
    if a is None:
        diz(f'{nome_app} existe no app', False, 'tabela nao encontrada')
        continue
    if b is None:
        diz(f'{fn} existe no script', False, 'funcao nao encontrada')
        continue
    av = [ms(x) for x in a]
    # entradas sem milissegundo (OFF, ---, ATIVO) valem 0 no script
    av = [0 if v is None else v for v in av]
    if len(av) != len(b):
        diz(f'{nome_app} x {fn} ({desc})', False,
            f'app tem {len(av)} valores, script tem {len(b)}')
        continue
    difs = [(i, av[i], b[i]) for i in range(len(av)) if av[i] != b[i]]
    diz(f'{nome_app} x {fn} ({desc})', not difs,
        f'{len(av)} valores iguais' if not difs
        else 'divergem: ' + '; '.join(f'idx {i}: app {x} ms, script {y} ms' for i, x, y in difs))

print('\n--- empacotamento a*R+b: quem tem de caber em R e o B ---')
# Erro que eu cometi na primeira versao deste conferidor: em (tin*20 + tout) o limitado e
# o TOUT, nao o TIN. O TIN so precisa que tin*R + (R-1) caiba no campo de bits.
# (operando A, operando B, radix, bits do campo, o que e)
PACK = [
    (r'm\.tin\*(\d+)\+m\.tout', 'THR', 'THR_OUT', 9, 'THR_IN x THR_OUT'),
    (r'm\.mult\*(\d+)\+m\.dir',  'MULT', 'DIR',     6, 'MULT x DIR'),
]
# quantas opcoes cada operando B oferece na tela
OPC_B = {'THR_OUT': None, 'DIR': 3}
mm = re.search(r"sel\(m\.tout,\['OFF'\]\.concat\(THR\.slice\(1(?:,\s*(\d+))?\)\)", app)
if mm:
    _t = tab_app('THR')
    OPC_B['THR_OUT'] = 1 + ((int(mm.group(1)) if mm.group(1) else len(_t)) - 1)
for pad, nome_a, nome_b, bits, desc in PACK:
    m2 = re.search(pad, app)
    if not m2:
        diz(f'empacotamento {desc}', False, 'padrao nao encontrado no app')
        continue
    R = int(m2.group(1))
    nb = OPC_B.get(nome_b)
    na = len(tab_app(nome_a) or [])
    if nb is None:
        diz(f'{nome_b} ({desc})', False, 'nao contei as opcoes')
        continue
    diz(f'{desc}: {nome_b} com {nb} opcoes num digito base {R}', nb <= R,
        f'indices 0..{nb-1}' if nb <= R else f'o indice {R} transborda para o {nome_a}')
    pior = (na - 1) * R + (R - 1)
    diz(f'{desc}: pior caso {pior} cabe em {bits} bits ({2**bits - 1})', pior < 2**bits,
        f'{nome_a} chega a {na-1}' if pior < 2**bits else 'ESTOURA o campo')

# o THR_OUT e oferecido com um recorte proprio
mm = re.search(r"sel\(m\.tout,\['OFF'\]\.concat\(THR\.slice\(1(,\s*(\d+))?\)\)", app)
if mm:
    fim = int(mm.group(2)) if mm.group(2) else len(tab_app('THR'))
    ofer = 1 + (fim - 1)
    diz(f'THR_OUT oferece {ofer} opcoes (indices 0..{ofer-1})', ofer <= 20,
        'cabe no digito base 20' if ofer <= 20 else f'o indice {ofer-1} transborda')
else:
    diz('o seletor de THR_OUT foi localizado', False, 'padrao nao encontrado')

print('\n--- o editor do OLED oferece o mesmo que o app? ---')
CLAMPS = [
    (r'if\(Wz_Cond_ThrIn > (\d+)\)', 'THR', 'THR_IN'),
    (r'if\(Wz_Cond_ThrOut > (\d+)\)', None, 'THR_OUT'),
    (r'if\(Wz_Fonte_Tipo > (\d+)\)', 'FONTES', 'FONTE'),
]
for pad, nome_app, desc in CLAMPS:
    mm = re.search(pad, g)
    if not mm:
        diz(f'limite do {desc} no OLED', False, 'clamp nao encontrado')
        continue
    teto = int(mm.group(1))
    if nome_app:
        a = tab_app(nome_app)
        diz(f'{desc}: OLED ate {teto}, app ate {len(a)-1}', teto == len(a) - 1,
            'iguais' if teto == len(a) - 1 else 'o OLED e o app oferecem faixas diferentes')
    else:
        diz(f'{desc}: OLED ate {teto}', teto == 19,
            'cabe no digito base 20' if teto == 19 else f'teto {teto} transborda')

print('\n--- os indices de botao e destino batem com o script? ---')
# BOTOES[0] = '---'; 1..16 tem de casar com Set_Btn_Fisico(idx) 0..15
bot = tab_app('BOTOES')
m = re.search(r'function Set_Btn_Fisico\(idx, val\)\s*\{(.*?)\n\}', g, re.S)
if bot and m:
    mapa = {int(a): b for a, b in re.findall(r'if\(idx == (\d+)\)\s*set_val\(PS5_(\w+),', m.group(1))}
    esp = [x.upper() for x in bot[1:]]
    got = [mapa[k] for k in sorted(mapa)][:len(esp)]
    difs = [(i + 1, esp[i], got[i]) for i in range(min(len(esp), len(got))) if esp[i] != got[i]]
    diz(f'BOTOES x Set_Btn_Fisico ({len(esp)} botoes)',
        not difs and len(esp) == len(got),
        'iguais, na mesma ordem' if not difs and len(esp) == len(got)
        else (f'app tem {len(esp)}, script tem {len(got)}' if len(esp) != len(got)
              else 'divergem: ' + '; '.join(f'idx {i}: app {a}, script {b}' for i, a, b in difs)))
else:
    diz('BOTOES x Set_Btn_Fisico', False, 'nao localizei um dos dois lados')

# DESTINOS[0] = '---'; 1..18 -> Acc_00..Acc_17 via Aplicar_Acc
dst = tab_app('DESTINOS')
m = re.search(r'function Aplicar_Acc\(\)\s*\{(.*?)\n\}', g, re.S)
if dst and m:
    ordem = re.findall(r'set_val\(PS5_(\w+),', m.group(1))
    esp = [x.upper() for x in dst[1:]]
    difs = [(i + 1, esp[i], ordem[i]) for i in range(min(len(esp), len(ordem))) if esp[i] != ordem[i]]
    diz(f'DESTINOS x Aplicar_Acc ({len(esp)} destinos)',
        not difs and len(esp) == len(ordem),
        'iguais, na mesma ordem' if not difs and len(esp) == len(ordem)
        else (f'app tem {len(esp)}, script tem {len(ordem)}' if len(esp) != len(ordem)
              else 'divergem: ' + '; '.join(f'idx {i}: app {a}, script {b}' for i, a, b in difs)))
else:
    diz('DESTINOS x Aplicar_Acc', False, 'nao localizei um dos dois lados')

print('\n--- tabelas por FORMULA: comparadas EXECUTANDO os dois lados ---')
# O THOLD tem 63 valores e e gerado por formula no app e no script. Reimplementar a
# formula em Python aqui faria o teste espelhar o que quer conferir. Os dois lados sao
# EXECUTADOS: o app em node, o script compilado em C.
import subprocess
import tempfile


def _formula_app():
    js = ('''const {JSDOM}=require('jsdom');const fs=require('fs');
const w=new JSDOM(fs.readFileSync(process.argv[2],'utf8'),{runScripts:'dangerously',
 url:'https://cdanv.github.io/D-Sig/',beforeParse(x){
  Object.defineProperty(x,'localStorage',{value:{getItem:()=>null,setItem(){},removeItem(){}}});
  x.matchMedia=()=>({matches:false,addListener(){},addEventListener(){}});
  x.navigator.serviceWorker={register:()=>Promise.resolve()};}}).window;
console.log(JSON.stringify(w.THOLD));''')
    with tempfile.NamedTemporaryFile('w', suffix='.js', delete=False) as f:
        f.write(js)
        p = f.name
    try:
        env = dict(os.environ)
        for base in (AQUI, os.path.join(AQUI, '..', 'teste')):
            nm = os.path.abspath(os.path.join(base, 'node_modules'))
            if os.path.isdir(os.path.join(nm, 'jsdom')):
                env['NODE_PATH'] = nm
                break
        r = subprocess.run(['node', p, APP], capture_output=True, text=True, env=env, timeout=120)
        if r.returncode != 0:
            return None, (r.stderr or '').strip().split('\n')[-1][:70]
        return json.loads(r.stdout.strip()), ''
    finally:
        os.unlink(p)


def _formula_script():
    SIM = None
    for c in ('sim', os.path.join('..', 'sim')):
        p = os.path.abspath(os.path.join(AQUI, c))
        if os.path.isfile(os.path.join(p, 'gpc2c.py')):
            SIM = p
            break
    if not SIM:
        return None, 'simulador nao encontrado'
    d = tempfile.mkdtemp(prefix='dsig_tab_')
    try:
        c = os.path.join(d, 's.c')
        r = subprocess.run([sys.executable, os.path.join(SIM, 'gpc2c.py'), GPC, c],
                           capture_output=True, text=True)
        if r.returncode != 0:
            return None, 'transpilar: ' + (r.stderr or '').strip().split('\n')[-1][:60]
        main = os.path.join(d, 'm.c')
        open(main, 'w').write('''#include "gpcrt.h"
int IV[64],OV[64],PV[64],PT[64],RT=10,PVAR[128];long OPS=0;
int RUMB=0,RUMBF=0,LEDS[4];int SCREEN=0,CLS=0,PRINTS=0;long NGET=0,NSET=0;
int Hphold_Tempo_Ms(int idx);
int main(void){int i;for(i=0;i<=62;i++)printf("%d\\n",Hphold_Tempo_Ms(i));return 0;}
''')
        exe = os.path.join(d, 'x')
        r = subprocess.run(['gcc', '-w', '-O1', f'-I{SIM}', '-o', exe, main, c],
                           capture_output=True, text=True)
        if r.returncode != 0:
            return None, 'gcc: ' + (r.stderr or '').strip().split('\n')[0][:60]
        r = subprocess.run([exe], capture_output=True, text=True)
        return [int(x) for x in r.stdout.split()], ''
    finally:
        import shutil
        shutil.rmtree(d, ignore_errors=True)


_a, _ea = _formula_app()
_b, _eb = _formula_script()
if _a is None or _b is None:
    diz('THOLD x Hphold_Tempo_Ms (tempo do GAMA HOLD)', False, _ea or _eb)
else:
    _am = [ms(x) for x in _a]
    _d = [(i, _am[i], _b[i]) for i in range(min(len(_am), len(_b))) if _am[i] != _b[i]]
    diz('THOLD x Hphold_Tempo_Ms (tempo do GAMA HOLD)',
        not _d and len(_am) == len(_b),
        f'{len(_am)} valores iguais, de {_b[0]} a {_b[-1]} ms' if not _d and len(_am) == len(_b)
        else (f'app tem {len(_am)}, script tem {len(_b)}' if len(_am) != len(_b)
              else 'divergem: ' + '; '.join(f'idx {i}: app {x}, script {y}' for i, x, y in _d[:5])))

print()
if falhas:
    print(f'  => {len(falhas)} divergencia(s): ' + '; '.join(falhas))
    sys.exit(1)
print('  => todas as tabelas batem entre o app e o script')
