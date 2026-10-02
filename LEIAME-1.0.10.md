# D-Sig 1.0.10 — o conserto do ZETA

## O que mudou

O `Config_Zeta()` era gerado pelo app com a numeração **fixa** dos MODs e rodava a cada
boot. Enquanto só o app editava a lista isso funcionava. No instante em que o aparelho
também pode deletar ou reordenar, reaplicar por posição está errado por construção — e o
boot seguinte carimbava a fiação antiga sobre a lista já deslocada.

Medido antes do conserto: deletar o MOD_05 do Mad Max deixava **12 de 14 slots com ZETA
errado** depois de religar, cada slot herdando a fiação do seu antecessor.

## O preço

**O teto caiu de 21 para 20 MODs**, no script e no app. As SPVARs 61, 62 e 63 — que
guardavam o MOD 21 — passaram a guardar a **permutação**: qual posição original da tabela
do app cada slot ocupa hoje.

| SPVAR | conteúdo | bits |
|---|---|---|
| 1 – 60 | 20 MODs × 3 palavras | — |
| 61 | permutação, slots 1-7 (base-21) | 0-30 |
| 62 | permutação, slots 8-14 (base-21) | 0-30 |
| 63 | permutação, slots 15-20 + **guarda `0b1010`** | 0-26 / 27-30 |
| 64 | migração (bit 0) + selo (bits 1-31) — intocada | — |

Os MODs 1 a 20 **mantêm exatamente as SPVARs de antes**: nada se moveu.

## A mudança central

O app parou de escrever em slot:

```gpc
DS_F1_EXCL_07=8; DS_F1_ASSOC_07=0; DS_F1_BLOQ_07=0;    // antes
Zeta_Um(7, 8, 0, 0);                                    // agora
```

e o script resolve o destino, remapeando também os bits da máscara pela mesma conta.
Cada original é escrito **uma vez**, no lugar certo, direto da constante do app — nada é
lido de volta, nada se atropela. Permutar as máscaras depois exigiria rascunho, e não há
vetor para rascunho nesta linguagem.

O `Zeta_Limpar()` é novo e obrigatório: original deletado tem de deixar o slot limpo, e
até a 1.0f ninguém limpava.

## A migração é automática

O selo é `hash(JSON.stringify(j.mods) + j.nome)`, e `j.mods` passou de 21 para 20
entradas — então **o selo muda para todos os jogos**, obrigatoriamente, e o
`Config_Inicial()` roda no primeiro boot escrevendo a permutação identidade.

O nibble de guarda é a segunda linha de defesa, para o jogo de selo 0 (InLoco) e para o
caso de você voltar à 1.0f e subir a 1.0h de novo.

**Se algum jogo seu tiver o MOD 21 configurado**, o app avisa na abertura e remove. Seu
jogo mais cheio (Mad Max) tem 17.

## O portão agora tem 12 verificações

| # | verifica | provado reprovando? |
|---|---|---|
| 1-2 | o avulso transpila, compila e sobrevive a 60.000 voltas de fuzz | sim (`circle_oled`) |
| 3-5 | o app gera, transpila, compila e sobrevive ao fuzz | sim |
| 6 | o TURBO do MOD_11 sai 150/50/150/50/150/50/250 ms | sim (tabela TPASSO) |
| 7 | o `DELETAR?` exige 1000 ms de TRIANGLE | sim (`TIME_TRI_DELETE`) |
| 8 | **o ZETA sobrevive a deletar um slot e religar** | sim (`Perm_Del` anulado) |
| 9 | **o ZETA sobrevive a reordenar e religar** | sim (`Perm_Troca` anulado) |
| 10 | **a EEPROM da 1.0f migra nos 3 estados** (zerada, com config, com lixo) | — |
| 11 | o script gerado não tem função órfã (GPC3005) | sim (âncoras removidas) |
| 12 | **jogo sem nenhum MOD** também não tem função órfã | sim (âncoras removidas) |
| — | toda escada de slot vai de 1 a MAX_INST, sem buraco | sim (degrau 19 removido) |

Os hashes de comportamento ficaram **idênticos aos da 1.0f** nos dois scripts: o conserto
não alterou nada em regime permanente, só o que acontece ao religar depois de editar no
aparelho.

## Compilado, e cabe

Os quatro Builds, com a 1.0h:

| script | binário | % do limite |
|---|---|---|
| InLoco | 52.032 | 79,42% |
| Cities Skylines | 52.336 | 79,88% |
| Football-FIFA-eFoot | 52.400 | 79,98% |
| Mad Max | 52.656 | 80,37% |

**0 erros nos quatro.** Variable slots 481/1024 (47,16%) e peak stack 512/1024 (50,00%),
idênticos em todos — são as globais, que não dependem do jogo. Sobram ~13.000 bytes.

### O aviso GPC3005, e o que ele revelou

A 1.0h dava `Function 'Zeta_Blk' is never called and has been removed`: 1 aviso no Cities,
1 no Football, **0 no Mad Max** e 5 no InLoco.

A causa: eu havia posto as chamadas-âncora no `Config_Zeta` do **template**, mas o app
substitui essa função **inteira** — então elas desapareciam em todo script gerado. E a
auditoria de função órfã do `embutir.py` só olhava o avulso.

Na 1.0i o **app** emite as três âncoras, sempre. Custo estimado: ~37 bytes, uma vez no
boot. Previsão: **0 avisos nos quatro**.

O portão ganhou duas verificações e um molde novo — um jogo **sem nenhum MOD**, porque o
Mad Max usa ZETA, FIN e BLOK ao mesmo tempo e por isso nunca produz órfã. Molde que não
consegue reprovar não prova nada: removi as âncoras de propósito e só o molde vazio
reprovou.

Depois disso, um teste no aparelho: deletar um MOD do meio, conferir o ZETA, **desligar e
ligar**, e conferir de novo.

## Mais duas coisas na 1.0.10

**Versão em número.** A 1.0a..1.0i eram letras, e com letra a regra "nunca anda para trás"
não era verificável — só dava para pegar "mesma letra, conteúdo diferente". Com número o
`embutir.py` EXIGE que a nova seja estritamente maior. A sequência fecha: a..i são 1 a 9,
e esta é a 10. O formato de letra ainda é lido para comparar com o histórico, mas recusado
para publicar.

| `DS_VERSAO` | decisão |
|---|---|
| `D-Sig 1.0i` | recusa — formato aposentado, sugere `1.0.10` |
| `D-Sig 1.0.8` | recusa — anterior ao publicado |
| `D-Sig 1.0.9` com conteúdo novo | recusa — mesma versão, conteúdo diferente |
| `D-Sig 1.0.10` | aceita → cache `dsig-1.0.10` |

**Cor por GAMA no app.** Cada alternativa com seu matiz e uma barra lateral agrupando os
sub-campos dela. Três das cinco cores do app já tinham significado (azul = acento,
vermelho = perigo, âmbar = aviso), então calculei cinco matizes novos: ≥40° de qualquer
reservado, ≥40° entre si, e todos com o **contraste do cinza atual** (6,68:1), para os
cinco rótulos pesarem igual — variação de 0,07. O `tira_foto.js` renderiza o app de
verdade no Chromium e fotografa a seção, para mudança visual ser vista e não descrita.

| GAMA | matiz | cor |
|---|---|---|
| 2CLK | 85° | `#84ad4a` |
| TOGGLE | 125° | `#51b459` |
| HOLD | 165° | `#4cb198` |
| AFTER | 262° | `#ac97d2` |
| BLOK | 312° | `#cd8bc0` |

## Os patches

`p15_slot20.py` (script 21→20), `p16_app20.py` (app 21→20 + migração da biblioteca),
`p17_perm.py` (a permutação), `p18_app_zeta.py` (o gerador por posição original), `p19_gama_cor.py` (a cor por GAMA).
Cada um com asserção em toda troca e conferência final própria.
