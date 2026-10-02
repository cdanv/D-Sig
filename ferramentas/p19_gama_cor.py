#!/usr/bin/env python3
"""Cor por GAMA no app: cada alternativa com seu matiz, e os sub-campos agrupados nele.

O PROBLEMA: a secao GAMA tem ate 11 linhas, todas no mesmo cinza. Um "· tempo" pertence
ao HOLD e um "· modo" ao AFTER, mas a unica pista disso e o ponto no comeco do rotulo.
Achar a alternativa certa exige ler de cima para baixo.

A ESCOLHA DAS CORES, e por que nao reaproveitei a paleta: o app tem cinco cores e ha cinco
GAMAs, o que parece encaixar — mas tres ja carregam SIGNIFICADO. O azul e o acento
primario (11 usos: titulos de secao, botoes, bordas), o vermelho e perigo (limite
estourado, apagar) e o ambar e aviso. Pintar um GAMA de vermelho o faria parecer erro.
So verde e rosa estavam livres, e dois nao bastam.

Entao calculei cinco matizes novos sob tres regras:
  1. a 40 graus ou mais de qualquer matiz reservado (ambar 45, azul 213, vermelho 0);
  2. a 40 graus ou mais um do outro;
  3. com o MESMO CONTRASTE do cinza atual (--dim, 6,68:1 sobre o painel).

A regra 3 e a que importa de verdade. Luminosidade HSL nao e perceptual: a 64% um
amarelo-verde pesa 9,4:1 e um violeta 5,0:1 — os rotulos ficariam com pesos diferentes e
a tela ganharia uma hierarquia que ninguem pediu. Resolvendo a luminosidade por busca
binaria no contraste, os cinco pesam igual: variacao de 0,07. O rotulo continua
SECUNDARIO ao valor, que e o que o Daniel pediu ao dizer "levemente diferente".

O AGRUPAMENTO e o ganho real, nao a cor em si: cada alternativa e seus sub-campos entram
numa caixa com barra lateral do matiz, e os sub-campos ficam no mesmo matiz com opacidade
menor. E o mesmo idioma que o app ja usa (border-left de 3px) e o analogo, numa linha, do
que os titulos de secao fazem com o border-bottom.
"""
import re
import sys

F = 'index.html'
s = open(F, encoding='utf-8').read()
n = 0

def _limites():
    m = re.search(r'<script type="text/plain" id="tpl">(.*?)</script>', s, re.S)
    assert m, 'template nao encontrado'
    return m.start(1), m.end(1)


def troca(velho, novo, nome, css=False):
    """css=True troca ANTES do template (a folha de estilo); senao, depois (o app).
    O limite e recalculado a cada chamada: inserir texto move o indice da seguinte."""
    global s, n
    ini, fim = _limites()
    a, b = (0, ini) if css else (fim, len(s))
    trecho = s[a:b]
    assert velho in trecho, f'{nome}: nao encontrado'
    assert trecho.count(velho) == 1, f'{nome}: {trecho.count(velho)}x'
    s = s[:a] + trecho.replace(velho, novo, 1) + s[b:]
    n += 1
    print(f'  ok  {nome}')


# --- 1. as cinco cores, junto das outras ------------------------------------
troca("  --amber:#fbbf24;",
      "  --amber:#fbbf24;\n"
      "  /* GAMA — um matiz por alternativa. Calculados, nao escolhidos a olho:\n"
      "     >=40 graus de qualquer matiz reservado (ambar 45, azul 213, vermelho 0),\n"
      "     >=40 graus entre si, e todos com o contraste do --dim (6,68:1 no painel),\n"
      "     para os cinco rotulos pesarem igual. Ver p19_gama_cor.py. */\n"
      "  --g-2clk:#84ad4a;  --g-tog:#51b459;  --g-hold:#4cb198;\n"
      "  --g-after:#ac97d2; --g-blok:#cd8bc0;",
      'as cinco cores do GAMA', css=True)

# --- 2. o grupo: barra lateral e rotulos no matiz ---------------------------
troca(".fld:last-child{border-bottom:none}",
      ".fld:last-child{border-bottom:none}\n"
      "/* Cada alternativa do GAMA e seus sub-campos numa caixa com barra lateral.\n"
      "   O primeiro .fld e a alternativa; os demais sao os sub-campos dela, e por\n"
      "   isso :not(:first-child) basta — nao precisa de classe nos sub-campos. */\n"
      ".gg{border-left:3px solid var(--gg);padding-left:11px;margin:0 0 7px}\n"
      ".gg .fld label{color:var(--gg)}\n"
      ".gg .fld:not(:first-child) label{opacity:.62}\n"
      ".gg .fld:last-child{border-bottom:none}",
      'CSS do agrupamento', css=True)

# --- 3. o helper e a secao GAMA remontada -----------------------------------
troca("""  var sg=document.createElement('section');sg.innerHTML='<h2>GAMA</h2>';
  sg.appendChild(fld('2CLK',sel(m.g2clk,BOTOES,function(v){m.g2clk=v;up()})));
  if(m.g2clk)sg.appendChild(fld('· modo',sel(m.fin2clk,['ALTERNA','FINALIZA'],function(v){m.fin2clk=v;up()})));
  sg.appendChild(fld('TOGGLE',sel(m.gTog,BOTOES,function(v){m.gTog=v;up()})));
  if(m.gTog)sg.appendChild(fld('· modo',sel(m.finTog,['ALTERNA','FINALIZA'],function(v){m.finTog=v;up()})));
  sg.appendChild(fld('HOLD',sel(m.gHold,BOTOES,function(v){m.gHold=v;up()})));
  if(m.gHold){
    sg.appendChild(fld('· tempo',sel(m.gHoldT,THOLD,function(v){m.gHoldT=v;up()})));
    sg.appendChild(fld('· modo',sel(m.gHoldM,['APOS','ATE'],function(v){m.gHoldM=v;up()})));
    sg.appendChild(fld('· liga/desl',sel(m.finHold,['ALTERNA','FINALIZA'],function(v){m.finHold=v;up()})))}
  sg.appendChild(fld('AFTER',sel(m.gAfter,BOTOES,function(v){m.gAfter=v;up()})));
  if(m.gAfter){sg.appendChild(fld('· atraso',sel(m.gAfterT,TAFTER,function(v){m.gAfterT=v;up()})));
    sg.appendChild(fld('· modo',sel(m.finAfter,['ALTERNA','FINALIZA'],function(v){m.finAfter=v;up()})))}
  sg.appendChild(fld('BLOK',sel(m.gBlok,BOTOES,function(v){m.gBlok=v;up()})));
  A.appendChild(sg);""",
      """  var sg=document.createElement('section');sg.innerHTML='<h2>GAMA</h2>';
  // Cada alternativa vira um GRUPO com barra lateral no seu matiz; os sub-campos entram
  // no mesmo grupo, no mesmo matiz com opacidade menor. E o que diz, sem ler, que o
  // "· tempo" e do HOLD e nao do AFTER.
  function gg(cor,campos){var d=document.createElement('div');d.className='gg';
    d.style.setProperty('--gg','var(--g-'+cor+')');
    campos.forEach(function(c){if(c)d.appendChild(c)});return d}
  sg.appendChild(gg('2clk',[
    fld('2CLK',sel(m.g2clk,BOTOES,function(v){m.g2clk=v;up()})),
    m.g2clk&&fld('· modo',sel(m.fin2clk,['ALTERNA','FINALIZA'],function(v){m.fin2clk=v;up()}))]));
  sg.appendChild(gg('tog',[
    fld('TOGGLE',sel(m.gTog,BOTOES,function(v){m.gTog=v;up()})),
    m.gTog&&fld('· modo',sel(m.finTog,['ALTERNA','FINALIZA'],function(v){m.finTog=v;up()}))]));
  sg.appendChild(gg('hold',[
    fld('HOLD',sel(m.gHold,BOTOES,function(v){m.gHold=v;up()})),
    m.gHold&&fld('· tempo',sel(m.gHoldT,THOLD,function(v){m.gHoldT=v;up()})),
    m.gHold&&fld('· modo',sel(m.gHoldM,['APOS','ATE'],function(v){m.gHoldM=v;up()})),
    m.gHold&&fld('· liga/desl',sel(m.finHold,['ALTERNA','FINALIZA'],function(v){m.finHold=v;up()}))]));
  sg.appendChild(gg('after',[
    fld('AFTER',sel(m.gAfter,BOTOES,function(v){m.gAfter=v;up()})),
    m.gAfter&&fld('· atraso',sel(m.gAfterT,TAFTER,function(v){m.gAfterT=v;up()})),
    m.gAfter&&fld('· modo',sel(m.finAfter,['ALTERNA','FINALIZA'],function(v){m.finAfter=v;up()}))]));
  sg.appendChild(gg('blok',[
    fld('BLOK',sel(m.gBlok,BOTOES,function(v){m.gBlok=v;up()}))]));
  A.appendChild(sg);""",
      'secao GAMA agrupada por matiz')

print(f'\nPARTE 19: {n} trocas')
# as cinco variaveis tem de existir e ser usadas
for c in ('2clk', 'tog', 'hold', 'after', 'blok'):
    assert f'--g-{c}:' in s, f'variavel --g-{c} nao declarada'
    assert f"gg('{c}'," in s, f"grupo '{c}' nao montado"
print('  as 5 cores declaradas e as 5 usadas')
open(F, 'w', encoding='utf-8').write(s)
print(f'  {F} gravado')
