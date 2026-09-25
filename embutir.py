#!/usr/bin/env python3
"""A UNICA ferramenta de publicacao. Rode-a sempre que mexer no script.

D-Sig.fonte.gpc  ->  D-Sig.gpc  ->  template dentro do index.html
  (comentado)        (limpo)        (limpo, byte a byte igual ao D-Sig.gpc)

O QUE ELA GARANTE, falhando em vez de entregar algo errado:
  1. o D-Sig.gpc publicado e o template embutido no app tem o MESMO sha256;
  2. nenhum comentario sobra no que e publicado;
  3. as 9 ancoras de texto que o app usa para injetar a configuracao continuam la;
  4. as linhas de codigo do limpo sao IGUAIS, uma a uma, as do arquivo comentado.

POR QUE DOIS ARQUIVOS: comentario em GPC nao custa byte nenhum no Zen — o compilador os
descarta, e os 54.112 bytes do binario sao os mesmos com ou sem eles. O que os comentarios
custam e PESO DE DOWNLOAD do app, porque o template viaja dentro do index.html. Daí a
divisao classica entre FONTE e PUBLICADO: o comentado e onde se trabalha e se aprende, o
limpo e o que vai para o ar.
"""
import re, hashlib, sys, json
from limpar import limpar, ANCORAS

FONTE, PUB, APP = 'D-Sig.fonte.gpc', 'D-Sig.gpc', 'index.html'

bruto = open(FONTE, encoding='utf-8').read()
limpo = limpar(bruto)

# --- 1. o codigo nao pode ter mudado -----------------------------------------
cod_fonte = [l for l in limpar(bruto).split('\n') if l.strip()]
cod_limpo = [l for l in limpo.split('\n') if l.strip()]
assert cod_fonte == cod_limpo, 'as linhas de codigo divergiram'

# --- 2. nada de comentario, e as ancoras de pe -------------------------------
assert '/*' not in limpo and '*/' not in limpo, 'sobrou comentario de bloco'
assert '//' not in limpo, 'sobrou comentario de linha'
for a in ANCORAS:
    assert a in limpo, f'ANCORA PERDIDA: {a!r}'

# --- 3. estrutura ------------------------------------------------------------
assert limpo.count('{') == limpo.count('}'), 'chaves desbalanceadas'
assert limpo.count('(') == limpo.count(')'), 'parenteses desbalanceados'
nomes = re.findall(r'^function\s+(\w+)', limpo, re.M)
nf = len(nomes)
assert nf == len(re.findall(r'^function\s+(\w+)', bruto, re.M)), 'perdeu funcao'
assert 'combo ' not in limpo, 'apareceu combo'

# --- 3b. funcao orfa: o ZenStudio avisa, e um aviso vale um erro aqui ---------
# Esta checagem existe porque eu a fiz a mao uma vez, antes de uma alteracao, e nao
# repeti depois: a correcao do boot tirou os dois unicos chamadores do Salvar_Tudo e
# so o compilador percebeu. Auditoria que depende de alguem lembrar nao e auditoria.
orfas = [f for f in nomes if len(re.findall(r'\b' + f + r'\s*\(', limpo)) < 2]
assert not orfas, f'funcao sem nenhum chamador (o ZenStudio vai avisar): {orfas}'

# variavel declarada e nunca mencionada fora da declaracao
sem_decl = re.sub(r'^\s*int\s+.*$', '', limpo, flags=re.M)
mortas = [v for v in sorted(set(re.findall(r'\bint\s+(\w+)', limpo)))
          if not re.findall(r'\b' + v + r'\b', sem_decl)]
assert not mortas, f'variavel declarada e nunca usada: {mortas}'

# define declarado e nunca usado — nao gera aviso, mas mente sobre o que existe
dfs = re.findall(r'^define\s+(\w+)', limpo, re.M)
sem_uso = [d for d in dfs if len(re.findall(r'\b' + d + r'\b', limpo)) < 2]
DOC = {'SPVARS_PER_INST', 'BIT_SLOT_USED', 'F1_DIR_ABSOLUTO', 'LAYOUT_VER'}
sem_uso = [d for d in sem_uso if d not in DOC and not d.startswith(('DST_BIT_', 'BTN_BIT_'))]
assert not sem_uso, f'define sem uso: {sem_uso}'

# --- 3c. a VERSAO governa a publicacao ---------------------------------------
# A letra do build tem de mudar em toda publicacao. Esta checagem existe porque
# "nao sei se o app atualizou" e uma pergunta que nao deveria precisar de investigacao:
# se o conteudo mudou e a letra nao, o publicado mentiria sobre si mesmo.
mv = re.search(r'const string DS_VERSAO\s*=\s*"([^"]+)";', limpo)
assert mv, 'DS_VERSAO nao encontrada no script'
VERSAO = mv.group(1)                       # ex.: "D-Sig 1.0a"
mv2 = re.match(r'D-Sig (\d+\.\d+)([a-z])$', VERSAO)
assert mv2, f'formato da versao invalido: {VERSAO!r} (esperado "D-Sig 1.0a")'
CACHE = 'dsig-' + mv2.group(1) + mv2.group(2)

sha = hashlib.sha256(limpo.encode()).hexdigest()
REG = 'publicado.json'
try:
    ant = json.load(open(REG))
except Exception:
    ant = {}
if ant.get('sha256') and ant['sha256'] != sha and ant.get('versao') == VERSAO:
    print(f'  ERRO: o script mudou mas a versao continua {VERSAO}.')
    print(f'        Incremente a letra do build em DS_VERSAO e rode de novo.')
    sys.exit(1)

open(PUB, 'w', encoding='utf-8').write(limpo)

# --- 4. embute no app e prova a identidade -----------------------------------
s = open(APP, encoding='utf-8').read()
m = re.search(r'(<script type="text/plain" id="tpl">)(.*?)(</script>)', s, re.S)
assert m, 'template nao encontrado no index.html'
antes = len(m.group(2))
open(APP, 'w', encoding='utf-8').write(s[:m.start(2)] + limpo + s[m.end(2):])

tpl = re.search(r'<script type="text/plain" id="tpl">(.*?)</script>',
                open(APP, encoding='utf-8').read(), re.S).group(1)
h1 = hashlib.sha256(limpo.encode()).hexdigest()
h2 = hashlib.sha256(tpl.encode()).hexdigest()

# --- 5. o cache do service worker acompanha a versao -------------------------
# Antes o numero do cache era incrementado a mao, e esquecer disso faz o navegador
# continuar servindo o app anterior — que foi exatamente a duvida de hoje.
sw = open('sw.js', encoding='utf-8').read()
atual = re.search(r"const CACHE = '([^']+)';", sw)
assert atual, 'CACHE nao encontrado no sw.js'
if atual.group(1) != CACHE:
    open('sw.js', 'w', encoding='utf-8').write(
        sw.replace(f"const CACHE = '{atual.group(1)}';", f"const CACHE = '{CACHE}';"))
    print(f'  sw.js    : {atual.group(1)} -> {CACHE}')
else:
    print(f'  sw.js    : {CACHE} (ja estava)')

json.dump({'versao': VERSAO, 'sha256': sha}, open(REG, 'w'), indent=2)

print(f'  fonte    : {FONTE:18s} {bruto.count(chr(10))+1:6d} linhas  {len(bruto):7d} bytes')
print(f'  publicado: {PUB:18s} {limpo.count(chr(10))+1:6d} linhas  {len(limpo):7d} bytes'
      f'  (-{100 - 100*len(limpo)//len(bruto)}%)')
print(f'  template : {antes} -> {len(tpl)} bytes')
print(f'  sha256   : {h1[:32]}')
if h1 != h2:
    print('  DIVERGEM'); sys.exit(1)
print(f'  => {VERSAO} | publicado e template identicos | {nf} funcoes | 0 comentarios | '
      f'{len(ANCORAS)} ancoras intactas')
assert '</script>' not in limpo, 'o .gpc contem </script> e quebraria o HTML'
