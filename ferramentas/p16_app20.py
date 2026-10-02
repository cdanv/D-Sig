#!/usr/bin/env python3
"""ETAPA 4a, lado do app: 21 MODs viram 20, e a biblioteca salva e migrada.

O PONTO QUE QUASE ME ESCAPOU: a biblioteca no localStorage tem arrays de 21 MODs. O selo
e hash(JSON.stringify(j.mods) + j.nome). Se o app continuasse carregando 21 posicoes, o
selo NAO mudaria ao subir a 1.0g — e a migracao deterministica que eu prometi ao Daniel
cairia, porque ela depende exatamente dessa mudanca de selo para o Config_Inicial() rodar
e escrever a permutacao identidade. Truncar na carga e o que faz a promessa valer.

O MOD 21 CONFIGURADO: nenhum jogo do Daniel chega a 17, mas truncar em silencio um MOD que
alguem configurou seria apagar trabalho sem avisar. Entao a carga registra o nome do jogo
e o app avisa uma vez. Nao tento mover o MOD 21 para um slot vago: isso renumeraria as
referencias ZETA dos outros, e conserto que mexe no que nao foi pedido e como bug nasce.

Introduz NMOD = 20 como UMA constante. Antes o 21 estava escrito a mao em cinco lugares;
com a constante, a proxima mudanca de teto e uma linha em vez de uma cacada.
"""
import re
import sys

F = 'index.html'
s = open(F, encoding='utf-8').read()
n = 0

# So o JavaScript do app: o template embutido e substituido inteiro pelo embutir.py.
mt = re.search(r'<script type="text/plain" id="tpl">(.*?)</script>', s, re.S)
assert mt, 'template nao encontrado'
LIM = mt.end(1)


def troca(velho, novo, nome, so_js=True):
    global s, n
    ini = LIM if so_js else 0
    cabeca, corpo = s[:ini], s[ini:]
    assert velho in corpo, f'{nome}: nao encontrado'
    assert corpo.count(velho) == 1, f'{nome}: {corpo.count(velho)}x'
    s = cabeca + corpo.replace(velho, novo, 1)
    n += 1
    print(f'  ok  {nome}')


# --- 1. a constante ----------------------------------------------------------
troca("function modVazio(){return{nota:''",
      "// v6: o teto de MODs. Era 21 escrito a mao em cinco lugares; virou constante\n"
      "// quando caiu para 20 para liberar as SPVARs 61-63 para a permutacao do ZETA.\n"
      "var NMOD=20;\n"
      "function modVazio(){return{nota:''",
      'constante NMOD = 20')

troca('function jogoVazio(){var m=[],i;for(i=0;i<21;i++)m.push(modVazio());',
      'function jogoVazio(){var m=[],i;for(i=0;i<NMOD;i++)m.push(modVazio());',
      'jogoVazio: 21 -> NMOD')

troca('var usado=false,k; for(k=0;k<21;k++) if(nomeMod(j,k)) usado=true;',
      'var usado=false,k; for(k=0;k<NMOD;k++) if(nomeMod(j,k)) usado=true;',
      'selo: varredura 21 -> NMOD')

troca('// máscara de 21 bits das relações ZETA\n'
      'function maskZeta(a){var v=0;a.forEach(function(k){v|=1<<k});return v}',
      '// máscara de NMOD bits das relações ZETA. O filtro é novo: uma referência a um\n'
      '// MOD acima do teto viria de biblioteca antiga e viraria um bit que o script não\n'
      '// tem onde ler.\n'
      'function maskZeta(a){var v=0;a.forEach(function(k){if(k<NMOD)v|=1<<k});return v}',
      'maskZeta: limita ao teto')

troca('j.mods.push(modVazio());       // e a lista continua com 21 posicoes',
      'j.mods.push(modVazio());       // e a lista continua com NMOD posicoes',
      'apagarMod: comentario')

# os dois laços do configGpc
for rot in ('Config_Inicial', 'Config_Zeta'):
    pass
q = s[LIM:].count('for(i=0;i<21;i++){')
assert q == 2, f'esperava 2 lacos de 21 no configGpc, achei {q}'
s = s[:LIM] + s[LIM:].replace('for(i=0;i<21;i++){', 'for(i=0;i<NMOD;i++){')
n += 2
print('  ok  configGpc: 2 lacos 21 -> NMOD')

# --- 2. a migracao da biblioteca salva ---------------------------------------
troca("""        if(mm.gAfterT>7)mm.gAfterT=5;});
      x.cores=x.cores.map(function(v){return v>=CORES.length?0:v})});""",
      """        if(mm.gAfterT>7)mm.gAfterT=5;});
      // v6: o teto caiu de 21 para 20. Truncar aqui e o que faz o selo mudar — e o
      // selo mudando e o que dispara o Config_Inicial() no primeiro boot da 1.0g, que
      // escreve a permutacao identidade. Sem isto a migracao da EEPROM dependeria do
      // nibble de guarda, que acerta 15 em 16 e nao e certeza.
      if(x.mods.length>NMOD){
        if(x.mods.slice(NMOD).some(function(mm){return mm&&mm.nota}))
          PERDIDOS.push(x.nome||'(sem nome)');
        x.mods=x.mods.slice(0,NMOD);
      }
      while(x.mods.length<NMOD) x.mods.push(modVazio());
      // referencia ZETA a um MOD que nao existe mais nao pode sobreviver a carga
      x.mods.forEach(function(mm){['excl','assoc','bloq'].forEach(function(r){
        if(mm[r]) mm[r]=mm[r].filter(function(t){return t<NMOD})})});
      x.cores=x.cores.map(function(v){return v>=CORES.length?0:v})});""",
      'carga: trunca a biblioteca ao teto novo')

troca('function ler(){try{',
      '// Jogos que tinham o MOD 21 configurado. O app avisa uma vez; nao tento mover o\n'
      '// MOD para um slot vago, porque isso renumeraria as referencias ZETA dos outros.\n'
      'var PERDIDOS=[];\n'
      'function ler(){try{',
      'lista de jogos com MOD 21 configurado')

# --- 3. o aviso, uma vez -----------------------------------------------------
troca("var D=ler()||base(), tela='cat', jg=0, md=0, modo='';",
      "var D=ler()||base(), tela='cat', jg=0, md=0, modo='';\n"
      "if(PERDIDOS.length){\n"
      "  setTimeout(function(){alert('O teto de MODs caiu de 21 para 20 nesta versão, '+\n"
      "    'para liberar memória do Cronus e corrigir o ZETA ao deletar MODs no aparelho.'+\n"
      "    '\\n\\nO MOD 21 destes jogos foi removido: '+PERDIDOS.join(', ')+\n"
      "    '\\n\\nConfira e reconfigure se precisar.')},400);\n"
      "}",
      'aviso de MOD 21 removido')

# --- 4. o texto de ajuda que afirma 21 ---------------------------------------
troca("['21 MODs','96 bits cada, ocupando 63 das 64 SPVARs. Não há bit livre.'],",
      "['20 MODs','96 bits cada, ocupando 60 das 64 SPVARs. Das 4 restantes, 3 guardam a "
      "permutação que mantém o ZETA correto ao deletar ou reordenar MODs no aparelho, e 1 "
      "guarda migração + selo.'],",
      'ajuda: 21 -> 20 MODs')

# --- 5. o cache do service worker ---------------------------------------------
# (o embutir.py cuida do sw.js; aqui so a conferencia de que nada ficou com 21)
sobra = []
for i, lin in enumerate(s[LIM:].split('\n'), 1):
    corpo = lin.split('//')[0]
    if 'PERDIDOS' in corpo or 'teto de MODs caiu' in corpo:
        continue              # o proprio texto do aviso fala do 21 que saiu
    if re.search(r'\b21\b', corpo):
        sobra.append((i, lin.strip()[:100]))
print(f'\nPARTE 16: {n} trocas')
if sobra:
    print(f'  SOBROU 21 no JavaScript em {len(sobra)} linhas:')
    for i, lin in sobra:
        print(f'    {i:5d}  {lin}')
    sys.exit(1)
print('  nenhum 21 solto no JavaScript do app')
open(F, 'w', encoding='utf-8').write(s)
print(f'  {F} gravado')
