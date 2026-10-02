#!/usr/bin/env python3
"""ETAPA 4b, lado do app: o Config_Zeta() passa a falar em POSICAO ORIGINAL.

ANTES o app escrevia no slot:          DS_F1_EXCL_07=8; ... Fin_07=10;
AGORA o app diz de quem e a relacao:   Zeta_Um(7, 8, 0, 0);  Zeta_Fin(7, 10);

Quem resolve o slot de destino e o script, consultando a permutacao gravada na EEPROM. E
por isso que o conserto funciona: a tabela do app deixa de depender de a lista nunca ter
sido mexida no aparelho.

O Zeta_Limpar() na primeira linha substitui o 'Work_A = Work_A;' que existia so para o
ZenStudio nao avisar "Empty function" — e faz um trabalho de verdade: original deletado
tem de deixar o slot limpo, e ate a 1.0f ninguem limpava.
"""
import re
import sys

F = 'index.html'
s = open(F, encoding='utf-8').read()
n = 0

mt = re.search(r'<script type="text/plain" id="tpl">(.*?)</script>', s, re.S)
assert mt, 'template nao encontrado'
LIM = mt.end(1)


def troca(velho, novo, nome):
    global s, n
    cabeca, corpo = s[:LIM], s[LIM:]
    assert velho in corpo, f'{nome}: nao encontrado'
    assert corpo.count(velho) == 1, f'{nome}: {corpo.count(velho)}x'
    s = cabeca + corpo.replace(velho, novo, 1)
    n += 1
    print(f'  ok  {nome}')


troca("""  // v7l: corpo nunca vazio — sem ZETA/BLOK/FIN o ZenStudio avisava "Empty function"
  L.push('    Work_A = Work_A;');
  for(i=0;i<NMOD;i++){
    var mz=j.mods[i]; n=String(i+1).padStart(2,'0');
    if(!nomeMod(j,i))continue;
    var ex=maskZeta(mz.excl), as=maskZeta(mz.assoc), bl=maskZeta(mz.bloq);
    if(ex||as||bl)L.push('    DS_F1_EXCL_'+n+'='+ex+'; DS_F1_ASSOC_'+n+'='+as+'; DS_F1_BLOQ_'+n+'='+bl+';');
    if(mz.gBlok)L.push('    Blk_'+n+'='+mz.gBlok+';');
    var fin=finReal(mz);   // v7e: nunca gera flag para gatilho que nao existe
    if(fin)L.push('    Fin_'+n+'='+fin+';');
  }""",
      """  // v6: a tabela deixou de escrever em SLOT e passou a declarar POSICAO ORIGINAL.
  // O script resolve o destino pela permutacao gravada na EEPROM — e e so por isso que
  // deletar ou reordenar MODs no aparelho sobrevive ao desligamento.
  // O Zeta_Limpar tambem resolve o "Empty function" que o Work_A=Work_A resolvia, e
  // ainda faz trabalho real: original deletado tem de deixar o slot limpo.
  L.push('    Zeta_Limpar();');
  for(i=0;i<NMOD;i++){
    var mz=j.mods[i], o=i+1;
    if(!nomeMod(j,i))continue;
    var ex=maskZeta(mz.excl), as=maskZeta(mz.assoc), bl=maskZeta(mz.bloq);
    if(ex||as||bl)L.push('    Zeta_Um('+o+', '+ex+', '+as+', '+bl+');');
    if(mz.gBlok)L.push('    Zeta_Blk('+o+', '+mz.gBlok+');');
    var fin=finReal(mz);   // v7e: nunca gera flag para gatilho que nao existe
    if(fin)L.push('    Zeta_Fin('+o+', '+fin+');');
  }""",
      'configGpc: Config_Zeta por posicao original')

# A nota de ajuda afirmava que o ZETA nao sobrevive ao reinicio. Deixou de ser verdade.
m = re.search(r'// O que NAO sobrevive ao reinicio: as relacoes ZETA e o tempo do GAMA AFTER\.',
              s[LIM:])
if m:
    troca('// O que NAO sobrevive ao reinicio: as relacoes ZETA e o tempo do GAMA AFTER.',
          '// v6: as relacoes ZETA AGORA sobrevivem ao reinicio, inclusive a delete e\n'
          '// reordenacao feitos no aparelho — a permutacao na EEPROM e o que garante.',
          'nota: o ZETA passou a sobreviver')

print(f'\nPARTE 18: {n} trocas')

# nenhuma escrita direta em slot pode sobrar no gerador
sobra = [l.strip()[:100] for l in s[LIM:].split('\n')
         if re.search(r"DS_F1_(EXCL|ASSOC|BLOQ)_'\+n|'    (Blk|Fin)_'\+n", l)]
if sobra:
    print('  SOBROU escrita direta em slot no gerador:')
    for l in sobra:
        print('   ', l)
    sys.exit(1)
print('  o gerador nao escreve mais em slot fixo')
open(F, 'w', encoding='utf-8').write(s)
print(f'  {F} gravado')
