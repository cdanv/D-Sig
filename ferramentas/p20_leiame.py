#!/usr/bin/env python3
"""Poe o LEIAME.md em dia com a 1.0.10.

POR QUE ISTO E TRABALHO DE VERDADE, e nao arrumacao: o Daniel perguntou se o projeto
chegou a versao final, e a resposta honesta estava no proprio documento — ele afirmava
que "todo tempo configurado no app sai 63% mais longo no jogo", conclusao que foi
REFUTADA em 01/10 (149,8 ms para 150 ms configurados). Ferramenta cujo README mente
sobre o comportamento dela nao esta pronta, por melhor que o codigo esteja.

A secao do relogio ja foi reescrita. Aqui ficam os outros tres descompassos:
  - 21 MODs / 63 das 64 SPVARs -> 20 MODs / 60, e as 61-63 na permutacao;
  - a versao em LETRA -> em NUMERO, com a regra agora verificavel;
  - a secao do ZETA que faltava, porque o conserto e desta versao.
"""
import re
import sys

F = 'LEIAME.md'
s = open(F, encoding='utf-8').read()
n = 0


def troca(velho, novo, nome):
    global s, n
    assert velho in s, f'{nome}: nao encontrado'
    assert s.count(velho) == 1, f'{nome}: {s.count(velho)}x'
    s = s.replace(velho, novo, 1)
    n += 1
    print(f'  ok  {nome}')


# --- 1. a memoria -------------------------------------------------------------
troca("""Cada MOD ocupa **3 SPVARs** de 32 bits — 96 bits, todos em uso. Com 21
MODs isso são 63 das 64 SPVARs.

A **SPVAR_64** não está livre: o bit 0 marca que a migração de layout já
foi feita, e os bits 1–31 guardam o selo da configuração gerada pelo app.
Cada um tem seu espaço para que um não apague o outro.""",
"""Cada MOD ocupa **3 SPVARs** de 32 bits — 96 bits, todos em uso. Com 20
MODs isso são 60 das 64 SPVARs. As quatro restantes:

| SPVAR | conteúdo |
|---|---|
| 61 | permutação, slots 1-7 (base-21) |
| 62 | permutação, slots 8-14 (base-21) |
| 63 | permutação, slots 15-20 + nibble de guarda (bits 27-30) |
| 64 | migração (bit 0) + selo da configuração (bits 1-31) |

**Nenhuma está livre.** O teto era 21 MODs até a 1.0i; caiu para 20 na
1.0.10 porque as SPVARs 61-63 passaram a guardar a **permutação** — qual
posição original da tabela do app cada slot ocupa hoje. Sem ela o ZETA
sai errado depois de deletar ou reordenar MODs no aparelho. O preço foi
um MOD, e a conta fechou exatamente: 60 + 3 + 1 = 64.""",
      'memoria: 21 -> 20 MODs e as SPVARs da permutacao')

troca('   SPVARs) por volta, e o selo no fim. As 21 levam ~210 ms.',
      '   SPVARs) por volta, e o selo mais a permutação no fim. As 20 levam ~200 ms.',
      'Boot_Persistir: 21 -> 20 instancias')

troca('| EEPROM zerada, app com 21 MODs | 128 | 64, em 21 voltas |',
      '| EEPROM zerada, app com 20 MODs | 128 | 63, em 20 voltas |',
      'tabela de gravacoes: 21 -> 20')

troca('O `Salvar_Tudo`, que gravava as 21 de uma vez, deixou de existir — era',
      'O `Salvar_Tudo`, que gravava as 20 de uma vez, deixou de existir — era',
      'Salvar_Tudo: 21 -> 20')

# --- 2. a versao --------------------------------------------------------------
troca('''const string DS_VERSAO    = "D-Sig 1.0f";
```

O número é a versão do **script**; a letra é o **build**, e ela muda em
toda publicação. Dessa string saem, automaticamente:

- o que aparece no **OLED**, no menu de status (OPTIONS);
- o título e a tela de Informações do **app**, que lê a string do próprio
  template embutido;
- o nome do cache do service worker (`dsig-1.0f`).

Assim os três nunca discordam. Se o OLED diz `1.0f` e o app diz `1.0g`,
o Cronus está com uma versão anterior gravada — e a resposta é olhar a
tela, não abrir arquivo.''',
'''const string DS_VERSAO    = "D-Sig 1.0.10";
```

São três números: `maior.menor.publicação`. O último muda em **toda**
publicação. Dessa string saem, automaticamente:

- o que aparece no **OLED**, no menu de status (OPTIONS);
- o título e a tela de Informações do **app**, que lê a string do próprio
  template embutido;
- o nome do cache do service worker (`dsig-1.0.10`).

Assim os três nunca discordam. Se o OLED diz `1.0.10` e o app diz
`1.0.11`, o Cronus está com uma versão anterior gravada — e a resposta é
olhar a tela, não abrir arquivo.

### De letra para número

As publicações 1.0a até 1.0i usavam letra. O problema não era estética:
com letra, a regra "nunca anda para trás" **não era verificável** — o
`embutir.py` só conseguia pegar *"mesma letra, conteúdo diferente"*. A
regra estava escrita aqui como se valesse, e era intenção, não auditoria.

Com número a comparação é aritmética, e o `embutir.py` **exige** que a
nova seja estritamente maior. A sequência fecha: `a`…`i` são 1 a 9, e a
seguinte é a 10. O formato de letra ainda é lido para comparar com o
histórico, e recusado para publicar.

| `DS_VERSAO` | decisão |
|---|---|
| `D-Sig 1.0i` | recusa — formato aposentado, sugere `1.0.10` |
| `D-Sig 1.0.8` | recusa — anterior ao publicado |
| `D-Sig 1.0.9` com conteúdo novo | recusa — mesma versão, conteúdo diferente |
| `D-Sig 1.0.9` com conteúdo idêntico | aceita — republicação sem mudança |
| `D-Sig 1.0.10` | aceita → cache `dsig-1.0.10` |''',
      'versao: letra -> numero')

troca('### A letra nunca anda para trás', '### A versão nunca anda para trás',
      'titulo: letra -> versao')
troca('''A **a 1.0e era idêntica à 1.0c**: a 1.0d acrescentou um painel de diagnóstico ao menu de
status e ele foi removido. Mesmo assim a letra avançou, em vez de a 1.0c ser
republicada — e a razão é a função da letra.

**A letra não identifica o conteúdo. Identifica a publicação.**

Republicar a 1.0c faria um Cronus com a 1.0d gravada mostrar `1.0d` no OLED enquanto o
app mostra `1.0c` — letra **maior** no aparelho que no app. E este documento diz que
letra maior no aparelho significa *app desatualizado*, que seria o contrário do que
aconteceu. O selo passaria a mentir exatamente na pergunta que ele existe para
responder: **qual build está gravada neste Cronus?**

Reverter conteúdo é normal. Reverter a letra quebra o único instrumento que responde
essa pergunta sem abrir arquivo.''',
'''A **1.0e era idêntica à 1.0c**: a 1.0d acrescentou um painel de diagnóstico ao menu de
status e ele foi removido. Mesmo assim a versão avançou, em vez de a 1.0c ser
republicada — e a razão é a função dela.

**A versão não identifica o conteúdo. Identifica a publicação.**

Republicar a 1.0c faria um Cronus com a 1.0d gravada mostrar `1.0d` no OLED enquanto o
app mostra `1.0c` — versão **maior** no aparelho que no app. E este documento diz que
versão maior no aparelho significa *app desatualizado*, que seria o contrário do que
aconteceu. O selo passaria a mentir exatamente na pergunta que ele existe para
responder: **qual build está gravada neste Cronus?**

Reverter conteúdo é normal. Reverter a versão quebra o único instrumento que responde
essa pergunta sem abrir arquivo.

O mesmo aconteceu entre a 1.0g e a 1.0h: a 1.0g foi a poda de 21 para 20 MODs, publicada
sozinha para ser verificada isolada, e a 1.0h trouxe a permutação. Duas publicações para
uma entrega — o preço de fazer em duas etapas, e valeu: se o portão tivesse reprovado
depois da segunda, saber-se-ia na hora se o defeito estava na poda ou na lógica nova.''',
      'a regra do nunca-para-tras, em numero')

print(f'\nPARTE 20: {n} trocas')
sobra = [(i, l.strip()[:90]) for i, l in enumerate(s.split('\n'), 1)
         if re.search(r'63% mais longo|problema aberto|Com 21\b|as 21 levam|letra do build', l)]
if sobra:
    print('  SOBROU afirmacao desatualizada:')
    for i, l in sobra:
        print(f'    {i:5d}  {l}')
    sys.exit(1)
print('  nenhuma afirmacao desatualizada sobre relogio, teto ou versao')
open(F, 'w', encoding='utf-8').write(s)
open('README.md', 'w', encoding='utf-8').write(s)
print(f'  {F} e README.md gravados')
