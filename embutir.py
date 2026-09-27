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

# const string declarada e nunca impressa. Entrou na 1.0b, quando GAME_NAME_3 e 4
# sairam da tela: se eu tivesse tirado so os print e esquecido as declaracoes, ficariam
# duas strings mortas no binario e o ZenStudio talvez nem avisasse.
strs = re.findall(r'^const string\s+(\w+)\s*=', limpo, re.M)
str_mortas = [v for v in strs if len(re.findall(r'\b' + v + r'\b', limpo)) < 2]
assert not str_mortas, f'const string declarada e nunca usada: {str_mortas}'

# --- 3e. o init SO LE E AGENDA -----------------------------------------------------
# Duas coisas sairam do init, cada uma depois de um problema: GRAVAR saiu na 1.0 (era a
# tempestade de set_pvar que travava o aparelho com a EEPROM zerada) e DESENHAR saiu na
# 1.0c. Esta checagem existe para que nenhuma das duas volte por descuido — e "por
# descuido" e o caso normal: acrescentar uma linha no init e a coisa mais natural do
# mundo quando se quer que algo aconteca no boot.
mi = re.search(r'\ninit \{(.*?)\n\}', limpo, re.S)
assert mi, 'init nao encontrado'
corpo_init = mi.group(1)
PROIBIDO_NO_INIT = ['set_pvar(', 'Update_OLED(', 'image_oled(', 'line_oled(',
                    'rect_oled(', 'print(', 'circle_oled(', 'pixel_oled(']
no_init = [p for p in PROIBIDO_NO_INIT if p in corpo_init]
assert not no_init, (f'o init voltou a gravar ou desenhar: {no_init}. '
                     'Gravar e do Boot_Persistir (primeira chamada do main); desenhar e '
                     'do Tela_Manter, na primeira volta. O cls_oled e a unica excecao.')

# --- 3f. a tela inicial depende de dois valores parecerem arbitrarios ---------------
# Com o init sem desenhar, quem pinta a tela do boot e o Tela_Manter, porque CurrentMode
# (0) e LastMode (-1) nascem DIFERENTES. Igualar os dois — ou tirar o redesenho — deixa o
# aparelho ligando com o OLED apagado, e mais nada quebra: a regressao seria silenciosa,
# que e a unica que este projeto nao tolera.
cm = re.search(r'^int CurrentMode\s*=\s*(-?\d+);', limpo, re.M)
lm = re.search(r'^int LastMode\s*=\s*(-?\d+);', limpo, re.M)
assert cm and lm, 'CurrentMode ou LastMode nao encontrados'
assert int(cm.group(1)) != int(lm.group(1)), (
    f'CurrentMode ({cm.group(1)}) e LastMode ({lm.group(1)}) ficaram IGUAIS: o aparelho '
    'vai ligar com o OLED apagado, porque e a diferenca entre eles que faz a primeira '
    'volta do main desenhar. Desde a 1.0c o init nao desenha mais.')
mt = re.search(r'function Tela_Manter\(\)\s*\{(.*?)\n\}', limpo, re.S)
assert mt, 'Tela_Manter nao encontrada'
assert re.search(r'if\(CurrentMode != LastMode\)\s*\{\s*Update_OLED\(\);', mt.group(1)), \
    ('o redesenho por mudanca de dominio saiu do Tela_Manter — e com o init sem '
     'desenhar, ele e o UNICO que pinta a tela inicial.')
assert 'Tela_Manter();' in re.search(r'\nmain \{(.*?)\n\}', limpo, re.S).group(1), \
    'Tela_Manter deixou de ser chamada pelo main'

# --- 3d. a ARTE nao pode cair onde o texto sera impresso --------------------------
# ESTA CHECAGEM EXISTE POR UM ERRO MEU, e ele merece ficar registrado: eu tinha uma
# conferencia que impedia desenho debaixo de texto, e ela aprovou 343 pixels de desenho
# que o print ia apagar. O motivo e que as FAIXAS de texto que a alimentavam estavam
# num dicionario que eu DIGITEI — duas faixas, onde o script imprimia quatro linhas.
# Conferencia vale o que vale o dado que a alimenta, e dado digitado a mao nao vale.
# Agora as faixas saem do proprio publicado, e a checagem roda na publicacao, nao
# quando eu lembrar de rodar.
#
# print(x, y, tam, fundo, VAR[0]) com fundo 1 pinta fundo preto proprio: APAGA o que
# estiver embaixo. A largura da faixa depende de quem escreve a string:
#   - as que o APP substitui (nome do jogo, nomes de dominio) tem conteudo desconhecido
#     na hora de publicar -> a faixa vai ate a margem, que e a hipotese conservadora;
#   - as fixas no script -> a faixa e o tamanho real do texto.
ALT_FONTE = {0: 10, 1: 17}
LARG_FONTE = {0: 7, 1: 12}
DO_APP = {'GAME_NAME_1', 'GAME_NAME_2', 'MODE_S1', 'MODE_S2', 'MODE_S3', 'MODE_S4'}
valores = dict(re.findall(r'^const string\s+(\w+)\s*=\s*"([^"]*)";', limpo, re.M))

# Funcoes AUXILIARES que imprimem, com a faixa que cada uma ocupa a partir dos seus
# argumentos. Elas existem porque uma tela nao imprime so com print: o painel de
# diagnostico usa Print_Num, e a tela de dominio delega o nome ao Nome_Dominio. Sem este
# registro a checagem ficaria CEGA exatamente para o que foi acrescentado por ultimo —
# e uma auditoria cega no ponto novo e pior que nenhuma, porque da a impressao de cobrir.
# O LARG_DIG so existe quando ha impressor de numeros no script. Ele entrou na 1.0d
# junto com o painel de diagnostico e saiu na 1.0e junto com ele — o registro de
# impressores fica, porque o proximo que aparecer ja nasce conferido.
_m = re.search(r'^define LARG_DIG\s*=\s*(\d+);', limpo, re.M)
_LD = int(_m.group(1)) if _m else 7
IMPRESSORES = {
    # Print_Num(v, x, y, casas): 'casas' digitos de largura LARG_DIG, fonte 0
    'Print_Num':    lambda a: (int(a[1]), int(a[2]), int(a[1]) + int(a[3]) * _LD - 1,
                               int(a[2]) + ALT_FONTE[0] - 1),
    # Selo_Marca(x, y): duas letras, fonte 0
    'Selo_Marca':   lambda a: (int(a[0]), int(a[1]), int(a[0]) + 2 * _LD - 1,
                               int(a[1]) + ALT_FONTE[0] - 1),
    # Nome_Dominio(n): imprime MODE_S1..4, que o app substitui -> faixa ate a margem
    'Nome_Dominio': lambda a: (12, 25, 127, 25 + ALT_FONTE[1] - 1),
}
DESENHOS = {'line_oled', 'rect_oled', 'image_oled', 'circle_oled', 'pixel_oled',
            'print', 'cls_oled'}

# QUAIS funcoes sao telas: as que o Update_OLED CHAMA, nao as que se chamam Tela_*.
# A primeira versao desta checagem casava o nome e pegava o Tela_Manter e o
# Tela_Redesenho, que sao o agendador de redesenho e nao desenham nada. Derivar do
# Update_OLED tambem faz a lista se manter sozinha: tela nova chamada de la entra na
# conferencia sem eu mexer aqui.
_uo = re.search(r'function Update_OLED\(\)\s*\{(.*?)\n\}', limpo, re.S)
assert _uo, 'Update_OLED nao encontrado'
TELAS_FN = sorted(set(re.findall(r'\b(Tela_\w+)\(', _uo.group(1))))
assert TELAS_FN, 'nenhuma funcao de tela encontrada no Update_OLED'

for nome in TELAS_FN:
    mfn = re.search(r'function ' + nome + r'\(\w*\)\s*\{(.*?)\n\}', limpo, re.S)
    assert mfn, f'{nome} e chamada pelo Update_OLED e nao existe'
    corpo = mfn.group(1)

    # Nenhuma chamada desconhecida numa funcao de tela: se alguem acrescentar um
    # impressor novo sem registra-lo acima, a publicacao para aqui em vez de publicar
    # uma tela cuja faixa de texto ninguem conferiu.
    for ch in set(re.findall(r'^\s*(\w+)\(', corpo, re.M)):
        assert ch in DESENHOS or ch in IMPRESSORES, (
            f'{nome} chama {ch}(), que nao esta em DESENHOS nem em IMPRESSORES do '
            'embutir.py. Se ele imprime, registre a faixa que ocupa; se so desenha, '
            'acrescente-o a DESENHOS. Tela nao conferida nao se publica.')

    faixas = []
    for x, y, tam, fundo, var in re.findall(
            r'print\((\d+),\s*(\d+),\s*(\d+),\s*([^,]+),\s*(\w+)\[0\]\)', corpo):
        if fundo.strip() != '1':
            continue                      # fundo 0 e transparente: nao apaga nada
        x, y, tam = int(x), int(y), int(tam)
        x1 = 127 if var in DO_APP else min(127, x + len(valores.get(var, '')) * LARG_FONTE[tam])
        faixas.append((var, x, y, x1, y + ALT_FONTE[tam] - 1))
    for imp, faz in IMPRESSORES.items():
        for args in re.findall(imp + r'\(([^)]*)\)', corpo):
            a = [t.strip() for t in args.split(',')]
            try:
                fx0, fy0, fx1, fy1 = faz(a)
            except ValueError:
                continue                  # argumento nao-literal: nao da para conferir
            faixas.append((f'{imp}()', fx0, fy0, min(127, fx1), fy1))

    desenhos = []
    for a, b, c, d in re.findall(r'line_oled\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),', corpo):
        a, b, c, d = int(a), int(b), int(c), int(d)
        desenhos.append(('line', min(a, c), min(b, d), max(a, c), max(b, d)))
    for a, b, w, h in re.findall(r'rect_oled\((\d+),\s*(\d+),\s*(\d+),\s*(\d+),', corpo):
        a, b, w, h = int(a), int(b), int(w), int(h)
        desenhos.append(('rect', a, b, a + w - 1, b + h - 1))
    # O tamanho da imagem vem da DECLARACAO DELA, casada pelo nome. A primeira versao
    # disto pegava o primeiro 'const image' do arquivo — funcionava com uma imagem so e
    # apontaria para a imagem errada no dia em que houvesse duas.
    for a, b, img in re.findall(r'image_oled\((\d+),\s*(\d+),[^,]+,[^,]+,\s*(\w+)\[0\]\)', corpo):
        m = re.search(r'const image\s+' + img + r'\[\]\s*=\s*\{\s*\{(\d+),\s*(\d+),', limpo)
        assert m, f'{nome}: imagem {img} usada e nao declarada'
        a, b = int(a), int(b)
        desenhos.append((img, a, b, a + int(m.group(1)) - 1, b + int(m.group(2)) - 1))

    for var, fx0, fy0, fx1, fy1 in faixas:
        for tipo, dx0, dy0, dx1, dy1 in desenhos:
            if dx0 <= fx1 and fx0 <= dx1 and dy0 <= fy1 and fy0 <= dy1:
                print(f'  ERRO {nome}: {tipo}({dx0},{dy0})-({dx1},{dy1}) cai na faixa de '
                      f'{var} (x {fx0}..{fx1}, y {fy0}..{fy1}) — o print vai apagar')
                sys.exit(1)

    # TEXTO CONTRA TEXTO, e este caso faltava: a checagem comparava texto contra desenho
    # e deixava passar dois print sobrepostos, que se apagam um ao outro. Achei o furo
    # tentando quebrar a propria checagem — movi um Print_Num para cima da linha da
    # versao e ela aprovou. Vale o registro: um teste que so confirma o que eu esperava
    # nao testa nada; o que serve e o que tenta reprovar o que ja passou.
    for i in range(len(faixas)):
        for j in range(i + 1, len(faixas)):
            a, ax0, ay0, ax1, ay1 = faixas[i]
            b, bx0, by0, bx1, by1 = faixas[j]
            if ax0 <= bx1 and bx0 <= ax1 and ay0 <= by1 and by0 <= ay1:
                print(f'  ERRO {nome}: as faixas de {a} (x {ax0}..{ax1}, y {ay0}..{ay1}) '
                      f'e {b} (x {bx0}..{bx1}, y {by0}..{by1}) se sobrepoem — um print '
                      'apaga o outro')
                sys.exit(1)

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
