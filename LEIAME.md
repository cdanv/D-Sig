# D-Sig — diário de engenharia

Este arquivo é para **quem vai mexer no código**: a arquitetura, o layout de
bits, as medições feitas no aparelho, e cada decisão com o motivo e o que ela
substituiu. É longo de propósito — e é o lugar onde o *porquê* mora.

Quem só quer usar o D-Sig deve ler o [`README.md`](README.md).

### O repositório

```
index.html          o app. Contém o D-Sig embutido como template
D-Sig.gpc           o script avulso, sem comentários, pronto para o Zen Studio
manifest.json       \
sw.js                >  o que o GitHub Pages precisa servir, junto do index.html
icone-*.png         /
README.md           a porta de entrada
LEIAME.md           este arquivo
ferramentas/        nada disto vai ao ar; é a bancada
  sim/              o simulador (7 arquivos)
  oled/             a arte do OLED
```

### A bancada

| arquivo | o que faz |
|---|---|
| `ferramentas/D-Sig.fonte.gpc` | **o mesmo script, comentado. É o único arquivo que se edita à mão** |
| `ferramentas/embutir.py` | **a única ferramenta de publicação.** Limpa, publica, embute, propaga a versão e recusa entregar algo errado |
| `ferramentas/limpar.py` | o removedor de comentários e a lista das 11 âncoras que o app usa |
| `ferramentas/testa_sim.py` | o portão de comportamento: 17 verificações que **executam** o script |
| `ferramentas/gera_molde.py` | **gera o molde sintético do portão** e declara os 34 itens de cobertura que ele tem de sustentar |
| `ferramentas/testa_tabelas.py` | confere tabela por tabela entre o app e o script, por valor |
| `ferramentas/testa_a11y.js` | nome acessível e alvo de toque, no Chromium de verdade |
| `ferramentas/testa_dom.js` | o nome dos domínios, pelas duas vias do app |
| `ferramentas/tira_foto.js` | renderiza o app e fotografa uma seção, para revisão visual |
| `ferramentas/publicado.json` | o SHA-256 da última publicação. É com ele que o `embutir.py` recusa republicar conteúdo novo sob a mesma versão |
| `ferramentas/oled/padrao.py` | **a fonte única da arte do OLED.** Dele saem os PNGs de revisão, o `timbre.png` e o código das telas |
| `ferramentas/oled/png2gpc.py` | PNG de 1 bit → `const image` do GPC, no formato que o compilador exige |
| `ferramentas/sim/` | **o simulador.** Sete arquivos: `gpc2c.py` (transpilador GPC→C), `gpcrt.h` (runtime das primitivas) e os cinco cenários em C — `harness`, `fuzz`, `tri`, `zeta`, `mig` |
| `ferramentas/empacotar.py` | monta o repositório no layout público **e roda o `embutir.py` de dentro da cópia**, reprovando se ele não publicar o mesmo SHA-256 |

A cadeia da arte é reproduzível a partir do repositório: `python3 oled/padrao.py`
grava o `timbre.png`, e o `oled/png2gpc.py` devolve deste os mesmos 300 bytes
que estão no `const image DS_TIMBRE` do publicado.

O portão precisa de `python3`, `gcc` e `npm i -g jsdom playwright`. Faltando o
playwright, a verificação de acessibilidade **reprova em voz alta** em vez de
pular em silêncio — teste que pula sem avisar é lido como teste que passou, e foi
exatamente assim que o simulador ficou três versões dormindo sem ninguém notar.

> **D-Sig é o nome final do projeto.** A 1.0 é a v7o reestruturada e
> auditada — mesmo comportamento, verificado saída por saída no
> simulador. Nenhuma referência ao nome anterior ficou no script nem no
> app. Vindo de uma versão anterior, leia *Atualizando de uma versão
> anterior* antes de publicar.

---

## Fonte de verdade

Três arquivos, e a ordem entre eles é fixa:

```
D-Sig.fonte.gpc  ->  D-Sig.gpc  ->  template dentro do index.html
  (comentado)        (limpo)        (limpo, byte a byte igual ao .gpc)
```

**Só se edita o `D-Sig.fonte.gpc`.** Os outros dois são gerados, e quem
os gera é o `embutir.py` — uma chamada, `python3 embutir.py`. Ele falha
em vez de entregar algo errado se:

- as linhas de código do limpo não forem iguais, uma a uma, às do
  comentado;
- sobrar qualquer comentário no que vai ser publicado;
- faltar uma das 11 âncoras de texto que o app usa para injetar a
  configuração;
- o `.gpc` e o template embutido não tiverem o mesmo SHA-256.

Editar o `D-Sig.gpc` direto é trabalho perdido: a próxima chamada do
`embutir.py` o sobrescreve.

### Por que comentado e limpo

Comentário em GPC **não custa byte nenhum no Zen** — o compilador os
descarta, e o binário tem o mesmo tamanho com ou sem eles. O que eles
custam é **peso de download do app**, porque o template viaja dentro do
`index.html`: com comentários são 361 KB, sem eles 182 KB. Daí a divisão
clássica entre fonte e publicado.

Os scripts que o app **gera** também saem limpos, pela mesma regra
(`limparGpc`, gêmea do `limpar.py`). Faz sentido: depois de gravado no
Cronus o script não pode mais ser extraído nem aberto no ZenStudio,
então comentário ali não serve a ninguém.

Qualquer outro arquivo com o app dentro — `sig_router_app.html` ou
nomes parecidos — é cópia antiga e deve ser apagado. Foi ter duas
cópias circulando que gerou um script com `FA_Cfg_01`, variável que
não existe desde a v5.

Qualquer outro arquivo com o app dentro — `sig_router_app.html` ou
nomes parecidos — é cópia antiga e deve ser apagado. Foi ter duas
cópias circulando que gerou um script com `FA_Cfg_01`, variável que
não existe desde a v5.

---

## Usar o app

Abra `https://cdanv.github.io/D-Sig/` no navegador.

No Chrome do Android, menu **⋮ → Instalar app**. No computador, o
botão **Instalar** aparece na barra de endereço. No iPhone,
**Compartilhar → Adicionar à Tela de Início**.

Instalado, abre em janela própria e funciona offline.

### Os dados

Ficam no navegador que abriu o app, **por aparelho**. Celular e
computador têm catálogos separados.

**Exportar é o seu único backup**: o Cronus não devolve o script
depois de gravado. Use **Exportar / importar** de vez em quando, e
para levar o catálogo de um aparelho para outro.

---

## Atualizando de uma versão anterior

O repositório passou de `sigrouter` para `D-Sig`, então o endereço mudou:
o app agora vive em `https://cdanv.github.io/D-Sig/`. Duas consequências,
e as duas pedem a mesma coisa — **exportar antes**:

- O app instalado aponta para o endereço antigo. O GitHub redireciona o
  endereço de um repositório renomeado, mas o service worker antigo
  continua servindo a versão que ele guardou, do cache, mesmo online.
  Instalar de novo a partir do endereço novo é o caminho limpo.
- A biblioteca é guardada no navegador sob uma chave, e a chave mudou de
  nome junto com o projeto. Não há leitura da chave antiga — foi uma
  escolha, para que nenhuma referência ao nome anterior ficasse no
  código.

**A ordem, em cada aparelho:**

1. Abra o app **antigo**, ainda instalado: **Exportar / importar →
   Exportar**. Guarde o arquivo (WhatsApp para si mesmo serve).
2. Desinstale o app antigo.
3. Abra `https://cdanv.github.io/D-Sig/` e instale. A biblioteca aparece
   **vazia** — é esperado.
4. **Exportar / importar → Importar** o arquivo do passo 1.

Rede de segurança: o navegador guarda os dados por **domínio**, não por
pasta, e o domínio não mudou. Se o arquivo do passo 1 se perder, os dados
antigos ainda estão ali sob a chave `sigrouter` — recuperáveis pelo
console do navegador com
`localStorage.setItem('dsig', localStorage.getItem('sigrouter'))`.

**A EEPROM do Zen é preservada.** O layout de bits não mudou (segue em
**5**), então os MODs já gravados continuam valendo, e o selo da
configuração também não muda de lugar. Nada a regravar.

**O cache do app se limpa sozinho** dentro do endereço novo: o
`activate` do service worker apaga todo cache cujo nome seja diferente
do atual, na primeira abertura.

---

## Gravar no Cronus

1. Configure o jogo no app.
2. **Gerar código → Baixar o D-Sig completo (.gpc)**.
3. Abra no ZenStudio, compile e grave num slot.

O script traz um selo. Ao ligar, se o selo do código diferir do
gravado, a configuração é aplicada e o selo registrado. Nos boots
seguintes nada é sobrescrito — então o que você editar pelo OLED e
salvar continua valendo. Gerar configuração nova muda o selo, e ela
volta a ser aplicada.

O Cronus comporta **5 scripts** ao mesmo tempo. A biblioteca do app
é ilimitada.

---

## Como a memória é usada

Cada MOD ocupa **3 SPVARs** de 32 bits — 96 bits, todos em uso. Com 20
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
um MOD, e a conta fechou exatamente: 60 + 3 + 1 = 64.

### O `init` só lê e agenda

Nem grava, nem desenha. As duas saídas foram pagas com problema real:

| saiu do `init` | quando | quem faz agora |
|---|---|---|
| **gravar** na EEPROM | 1.0 | `Boot_Persistir`, primeira chamada do `main` |
| **desenhar** no OLED | 1.0c | `Tela_Manter`, na primeira volta do `main` |

Tirar o desenho foi de graça: o `Tela_Manter` compara `CurrentMode` com `LastMode`, e
os dois nascem **diferentes de propósito** — `0` e `-1`. A primeira volta do `main` pinta
a tela, ~10 ms depois do boot.

> **Igualar os dois apaga a tela inicial do aparelho e mais nada quebra** — regressão
> silenciosa, a única que este projeto não tolera. O `embutir.py` recusa publicar se
> `CurrentMode` e `LastMode` nascerem iguais, se o redesenho sair do `Tela_Manter`, ou se
> qualquer `set_pvar`, `print`, `line_oled`, `rect_oled` ou `image_oled` voltar ao `init`.
> O `cls_oled` é a única exceção: limpar não é desenhar, e é ele que apaga o display do
> firmware.

**Efeito colateral, e é ganho:** ligado só ao PC, onde o `main` não roda, o OLED fica
apagado. Antes mostrava a tela de identidade, desenhada pelo `init` — aparência que
sugeria "o script está rodando" quando só o `init` havia rodado. Agora **tela acesa
significa `main` rodando**, e isso é informação verdadeira.

### Gravação: nunca no `init`

A EEPROM do Cronus é frágil — a documentação a descreve como *rated for
1000's of* ciclos de leitura/gravação — e gravar nela é lento. Duas
regras, as duas nascidas de uma pane real:

1. **O `init` não grava.** Ele só lê e **agenda**. Quem grava é o
   `Boot_Persistir`, na primeira linha do `main`: uma instância (3
   SPVARs) por volta, e o selo mais a permutação no fim. As 20 levam ~200 ms.
2. **Só se grava o que mudou.** Todo `set_pvar` passa pelo `Grava_Spv`,
   que lê antes e desiste se o valor já está lá. Leitura não desgasta.

**O que isso NÃO resolve:** a pane com a mensagem **"Zen Bootloader
E3002"**. Esse código significa, na documentação do Cronus, que *o
firmware está corrompido ou ausente* — causado por gravação de firmware
interrompida, **perda de energia durante gravação**, ou arquivo corrompido.
Um script GPC não alcança a imagem do firmware; quando o bootloader
falha, o script nem chega a rodar. Se isso acontecer: botão de reset
embaixo do aparelho segurado ao conectar na porta CONSOLE/PC, depois
`firmware.modcentral.ca` no Chrome ou Edge. Falhando a gravação, a causa
usual é **alimentação USB insuficiente** — conecte também a porta PROG,
do lado direito.

O que a gravação diferida resolveu: depois de uma **limpeza de slots** a
EEPROM fica zerada, e nesse boot os dois caminhos de gravação do `init`
entravam juntos — 64 gravações seguidas no script avulso, 128 no script
do app, sem devolver o controle ao firmware. O Cronus travava piscando
vermelho e só voltava com hardreset. Do segundo boot em diante não havia
gravação nenhuma, e era por isso que o hardreset parecia "resolver".

| cenário | antes | depois |
|---|---|---|
| EEPROM zerada, avulso ou InLoco | 64 | **1** |
| EEPROM zerada, app com 20 MODs | 128 | 63, em 20 voltas |
| migração de layout antigo | 64 | **4** |
| regerar script com 1 MOD alterado | 64 | **2** |
| boot normal | 0 | 0 |
| **pico numa só passagem** | **128** | **3** |

Precisando espaçar ainda mais, o passo a dividir é o `Boot_Persistir`:
um SPVAR por volta em vez de três levaria 63 voltas (~630 ms) e exigiria
um dispatch por SPVAR.

O `Salvar_Tudo`, que gravava as 20 de uma vez, deixou de existir — era
ele que o `init` chamava nos dois pontos que causavam a pane.

## O que não é gravado na EEPROM

Três variáveis vivem em RAM: as relações **ZETA**, o botão do **GAMA
BLOK** e o **modo FINALIZA** dos gatilhos.

Se o script vier do app, eles são reaplicados a cada boot — a
configuração do app funciona como o padrão deles. Configurando só
pelo OLED, se perdem ao desligar.

O app marca esses MODs com a etiqueta **RAM**.

---

## Como o script é organizado

O `D-Sig.gpc` tem **19 seções numeradas na ordem física do arquivo**, e
o índice está no cabeçalho dele. Três regras valem para tudo:

- **`main` é um índice.** Nove chamadas, nenhuma lógica, e a ordem
  delas é funcional — a última, `Saidas_Manter`, existe para que o que
  ela escreve não possa ser sobrescrito por ninguém na mesma volta.
- **Não há combo nenhum.** Toda saída com duração é um contador em ms
  que perde `get_rtime()` (seção 18). Combo tem relógio próprio, uma
  instância só, e `combo_run` num combo em curso não reinicia nada —
  o que vira bug no dia em que o comando é repetido rápido.
- **Todo tempo é um `define` na seção 2**, com o nome do que mede.

Mexendo no script: seção nova entra no índice do cabeçalho, e o número
segue a ordem física.

---

## A arte do OLED

Três telas desenhadas, e o nome delas no script diz onde vivem:

| função | quando aparece | o que mostra |
|---|---|---|
| `Tela_Identidade` | nenhum domínio ativo | o timbre "D-Sig" + régua + nome do jogo em duas linhas |
| `Tela_Dominio(n)` | domínio 1 a 4 | quatro blocos, o ativo em **vídeo invertido**, e a derivação ativa no rodapé |
| `Tela_Status` | menu do OPTIONS | as réguas do título e da versão + o motivo do **sinal cortado** |

O motivo do sinal aparece **só onde carrega informação** — no domínio diz qual saída
está ativa, no status diz que o sinal está interrompido. Na tela de identidade seria
papel de parede, e papel de parede em 128×64 é desperdício de um espaço que não existe.

### Primitiva, não bitmap

Há **uma única imagem** no script, o timbre (`DS_TIMBRE`, 80×30, 300 bytes), e ela se
justifica sozinha: o `print` só tem fonte 0 (10px) e fonte 1 (17px), e aquele "D-Sig"
tem 30px de altura. Todo o resto é `line_oled` e `rect_oled`.

Os dois custos, **medidos no compilador** e não estimados:

| | custo |
|---|---|
| `const image` | 1 byte de binário por byte de dado |
| chamada de primitiva | ~12,3 bytes |

Daí a regra: **imagem compensa quando substitui mais de `bytes_da_imagem / 12` primitivas.**
As sete telas em bitmap davam 5.849 bytes; em primitiva dão ~742. O ganho maior está nos
domínios — quatro telas que diferem em dois detalhes viram **uma função parametrizada**
pelo `Igual(n, k)`, 252 bytes contra 3.488. Bitmap não sabe parametrizar.

### O formato do `const image`

Quem o fixou foi o compilador, não a documentação, que não menciona `image_oled` nem o
tipo `image`. A mensagem **GPC5116** diz que o número de valores é
`2 + ceil(larg * alt / 8)` — ou seja **fluxo contínuo de bits**, MSB primeiro, sem
enchimento no fim da linha.

Toda largura de imagem é **múltipla de 8**, de propósito: aí o empacotamento por linha e
o contínuo produzem os mesmos bytes, e a ordem dos bits no cruzamento de linha deixa de
ser uma pergunta. Custa no máximo 7 colunas de preto e compra a garantia.

### A faixa de texto é proibida, e a conferência é do `embutir.py`

`print(x, y, tam, 1, ...)` pinta fundo preto próprio: **apaga o que estiver embaixo**.
Desenhar ali não é só desperdício, é invisível — ninguém descobre o erro olhando a tela.

O `embutir.py` extrai as faixas **do próprio publicado**, lendo as chamadas de `print`
das funções de tela, e recusa publicar se qualquer `line_oled`, `rect_oled` ou
`image_oled` cair dentro de uma. Para as strings que o app substitui (nome do jogo,
nomes de domínio) a faixa vai até a margem, porque o conteúdo é desconhecido na hora de
publicar; para as fixas no script, é o tamanho real do texto.

> Esta checagem nasceu de uma falha: existia uma conferência com a mesma finalidade, e
> ela **aprovou 343 pixels** de desenho que o `print` ia apagar. As faixas que a
> alimentavam estavam num dicionário digitado à mão — duas faixas, onde o script
> imprimia quatro linhas. Conferência vale o que vale o dado que a alimenta.

### O nome do jogo tem duas linhas

Eram quatro até a 1.0b, e as duas últimas estavam **mortas por construção**: o app corta
o nome em 20 caracteres (`slice(0,10)` e `slice(10,20)`) e sempre gravava `""` nelas.
Reservavam `y 35..59` da tela inicial para não mostrar nada — e é nesse espaço que o nome
mora agora, com o timbre em cima. Foram **duas âncoras a menos** na lista do `limpar.py`.

---

## O relógio do firmware — medido, e RESOLVIDO

**Os tempos estão corretos.** Com o `VM SPEED` em 10 ms, uma duração configurada em
150 ms sai em **149,8 ms** e uma pausa de 50 ms sai em **50,1 ms**.

### O que parecia errado

Em 27/09 as medidas davam **1,63× mais longo que o configurado**, de forma consistente:
16 medidas, fator médio 1,630, desvio padrão 0,030. A conclusão registrada aqui era que
o `get_rtime()` mentia, reportando os 10 ms nominais enquanto a volta durava 16,3 ms.

**Estava errada** — ou melhor, estava certa sobre aquela sessão e errada sobre o script.

### Como se descobriu

Repetindo a medição em 01/10 com o `VM SPEED` em 10 ms e em 40 ms, e medindo a **largura
da rampa** do traço, que é um intervalo de amostragem (o PLOT liga dois pontos com reta,
e o botão é binário — a subida de 0 a 100 ocupa exatamente uma amostra):

| | rampa | amostras/s | ms por volta | pulso (150 ms) | pausa (50 ms) |
|---|---|---|---|---|---|
| captura de 27/09 | 22 px | 67 | **14,9** | 242,9 ms | 81,7 ms |
| 01/10, VM SPEED 10 ms | 12,2 px | 102 | **9,8** | **149,8 ms** | **50,1 ms** |
| 01/10, VM SPEED 40 ms | 43,6 px | 28,6 | **34,9** | 159,9 ms | 79,4 ms |

Na captura antiga o pulso mede **15,06 voltas** e a pausa **5,06** — exatamente as 15 e 5
voltas que 150 e 50 ms pedem a 10 ms. **O script sempre contou certo.** O que variou foi
a duração da volta: 16,1 ms naquela sessão, 10,0 ms depois.

Com 40 ms o pulso sai em 160 ms e a pausa em 80 — que são **4 e 2 voltas de 40 ms**. É
quantização, não erro: 150 ms só é alcançado na 4ª volta. E a razão dos períodos,
240 ÷ 200 = 1,20, bate com a previsão da quantização, 1,20.

### O que isso impediu

A alternativa em cima da mesa era **compensar as tabelas `TLAT` e `TPASSO`** dividindo-as
por 1,63. Com a VM a 10 ms isso produziria tempos 63% **curtos**. A medição serviu para
impedir uma mudança, não para autorizar uma.

### O que fica em aberto

**Por que a VM rodou a 16,1 ms naquela sessão.** Não se sabe, e não é reproduzível. O
script não mede a própria velocidade — foi a razão declarada para remover o painel de
diagnóstico da 1.0d, e continua valendo: medindo-se por dentro, ele não detecta um
`get_rtime()` mentiroso.

**O sintoma, e como conferir:** se um dia os tempos saírem longos, a primeira coisa a
olhar é a **largura da rampa no PLOT**, não o script. Rampa larga = volta longa.

### Um erro de método que vale registrar

O primeiro teste proposto era ler o **FPS do PLOT** com o `VM SPEED` em 40 ms, esperando
que caísse de 62 para 25. Caiu — e **não provou nada**: 62 também é, aproximadamente, a
taxa de atualização da tela do navegador, então as duas hipóteses previam 25. O que
separou foi a rampa, que mostrou 102 amostras/s a 10 ms — número que a hipótese "o PLOT
trava em 62" não produz.

*Teste que confirma as duas hipóteses não é teste.*

---

## PASSIVO engole os botões do GAMA

O `Suprime_Gatilhos()` zera **todos** os botões de GAMA de um MOD passivo — BLOK, 2CLK,
TOGGLE, HOLD e AFTER —, inclusive os marcados como **FINALIZA**, que só desligam. É a
supressão da ENTRADA, e ela vale para o botão, não para o MOD: o MOD responde
normalmente; o que não chega ao jogo é o botão.

A saída do DELTA sobrevive: o `Aplicar_Acc()` roda **por último** no `Run_Pipeline()`,
depois de toda supressão. Então um MOD pode escrever num botão que outro MOD passivo
suprime, e a escrita vale.

> Isto foi relatado como bug — *"no Mad Max o TRIANGLE não funciona"*. O `MOD_07`
> estava em PASSIVO com o TRIANGLE no AFTER. O comportamento estava certo; faltava a
> tela dizer. Desde a 1.0f o app mostra a observação, com o nome dos botões e dos
> domínios afetados.

---

## O ZETA e a permutação

Até a 1.0i, deletar ou reordenar um MOD **no aparelho** acertava as relações ZETA em RAM
e as perdia no desligamento seguinte. Medido no simulador: deletar o MOD_05 do Mad Max
deixava **12 de 14 slots com ZETA errado** depois de religar, cada slot herdando a fiação
do seu antecessor.

### A causa

O `Config_Zeta()` é gerado pelo app com a numeração **fixa** dos MODs e roda a **cada
boot**:

```gpc
DS_F1_EXCL_07=8; DS_F1_ASSOC_07=0; DS_F1_BLOQ_07=0;
```

Enquanto só o app edita a lista, isso funciona. No instante em que o aparelho também pode
deletar ou reordenar, reaplicar por posição está **errado por construção** — não é um
descuido, é uma premissa que deixou de valer. O boot carimbava a fiação antiga sobre a
lista já deslocada.

As máscaras ZETA não cabem na EEPROM: são 3 × 20 bits por MOD, e as três palavras de cada
MOD já estão com os 96 bits ocupados. Por isso elas sempre foram reaplicadas a cada boot.

### O conserto

Três palavras guardam **qual posição original cada slot ocupa hoje** (dígito 0 = MOD
criado no aparelho, que não existe na tabela do app), e o app passou a declarar de quem é
a relação em vez de escrever no slot:

```gpc
Zeta_Limpar();              // original deletado tem de deixar o slot limpo
Zeta_Um(7, 8, 0, 0);        // "o original 7 tinha estas relações"
Zeta_Fin(7, 10);
```

O script resolve o destino com `Perm_Onde(7)` e remapeia os bits da máscara pela mesma
conta. **Cada original é escrito uma vez, no lugar certo, direto da constante do app** —
nada é lido de volta, nada se atropela. Permutar as máscaras depois exigiria rascunho, e
não há vetor para rascunho nesta linguagem.

### Base-21, e por quê

5 bits por dígito dariam 6 dígitos por palavra — 18 em três palavras, faltariam dois.
Base-21 dá **7 por palavra**, porque 21⁷ = 1.801.088.541 ainda cabe em 31 bits. E 21
valores são exatamente o necessário: 20 posições mais o zero. Base-22 estouraria com 7
dígitos.

O bit 31 fica **fora**: ligado, a palavra vira negativa e a divisão com sinal desmonta a
base-21 errado. O nibble de guarda mora nos bits 27-30 da palavra 63, que só usa 27.

### A migração é determinística

O selo é `hash(JSON.stringify(j.mods) + j.nome)`, e `j.mods` passou de 21 para 20
entradas — então o selo **muda para todos os jogos**, obrigatoriamente, e o
`Config_Inicial()` escreve a permutação identidade no primeiro boot.

O nibble de guarda é a segunda linha: protege o jogo de selo 0 (o InLoco) e o caso de
voltar a uma versão de letra e subir a 1.0.10 de novo, quando as SPVARs 61-63 chegam com
configuração do antigo MOD 21. Testado nos três estados — zeradas, com configuração de
MOD e com lixo: nos três a identidade entra.

### Três armadilhas evitadas de propósito

1. **Contador de laço compartilhado.** A linguagem não tem variável local, então todo
   contador é global. `Perm_Mapear` roda um `while` e chama `Perm_Onde`, que roda outro,
   que chama `Perm_Carga`. Três níveis, três conjuntos de auxiliares distintos. Um nome
   repetido ali é um laço que nunca termina.
2. **Escrita no `init`.** O `Perm_Carregar()` não grava: quando a permutação é inválida
   ele conserta a RAM e **agenda**, e quem grava é o `Boot_Persistir`, no `main` — o mesmo
   caminho que a configuração do app já usava.
3. **Função órfã no script GERADO.** As chamadas-âncora estavam no `Config_Zeta` do
   template, mas o app substitui essa função **inteira** — elas sumiam em todo script
   gerado, e a auditoria só olhava o avulso. Quatro Builds deram 1, 1, 0 e 5 avisos
   GPC3005. Agora o **app** emite as âncoras, e o portão tem um molde de jogo **sem
   nenhum MOD** — porque o Mad Max usa ZETA, FIN e BLOK ao mesmo tempo e por isso nunca
   produz órfã. *Molde que não consegue reprovar não prova nada.*

---

## Apagar um MOD: app e script com a mesma semântica

Até a 1.0e o app fazia `j.mods[md] = modVazio()` — zerava o slot e ficava na tela. O
script sempre fez outra coisa (`Ajustar_Refs`, `Compactar_Lista`, `Zerar_Posicao`), e a
diferença foi **medida, não suposta**:

| | app até a 1.0e | script, e app desde a 1.0f |
|---|---|---|
| a lista | deixava **buraco** | **compacta**: o MOD_11 vira MOD_10 |
| as relações ZETA | mantinha os índices velhos | tira o apagado e **desce os de cima** |
| a tela | ficava no editor, agora em branco | **volta para o jogo** |

O buraco tinha consequência: gerando o script depois de apagar o MOD_10, os slots usados
saíam `1..9, 11..17`. O `Count_Instances` conta 16, o `Print_Inst_Row` desenha as linhas
1 a 16, a linha do slot vazio sai em branco e **o último MOD roda mas fica fora da
lista** — inalcançável para editar ou apagar pelo OLED.

E a tela que não mudava era o que fazia parecer que nada havia acontecido. Funcionava, e
parecia não funcionar — foi assim que chegou como *"a função de deletar não está
respondendo"*.

---

## O timbre

Até a 1.0e era a fonte bitmap de 10 px do gerador **ampliada 3×** com NEAREST: cada pixel
virava um quadrado de 3×3, então toda curva ganhava degrau de 3 px e todo traço tinha 3 px
de espessura por acidente. **Ampliar não é desenhar** — a letra de 10 px foi projetada
para 10 px.

Desde a 1.0f é **DejaVu Sans Bold rasterizada em 30 px** e limiarizada em 128. A escada
que sobra é a que o desenhista da fonte previu para este corpo. Custa **319 bytes contra
300** — 19 bytes.

> Antes disso eu tentei desenhar as letras à mão, pixel por pixel, com espessura constante
> e cantos chanfrados. Ficou **pior** que o original: o S virou um 5 e o g não fechou a
> tigela. Desenhar tipo é trabalho de quem desenha tipo; usar uma fonte feita não é a
> saída preguiçosa, é a correta.

---

## Versionamento e publicação

A versão vive em **um lugar só**, no `D-Sig.fonte.gpc`:

```gpc
const string DS_VERSAO    = "D-Sig 1.0.10";
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
| `D-Sig 1.0.10` | aceita → cache `dsig-1.0.10` |

### A versão nunca anda para trás

A **1.0e era idêntica à 1.0c**: a 1.0d acrescentou um painel de diagnóstico ao menu de
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
depois da segunda, saber-se-ia na hora se o defeito estava na poda ou na lógica nova.

**Publicar:**

1. Mexa no `D-Sig.fonte.gpc` — nunca no `D-Sig.gpc`.
2. **Incremente a letra** em `DS_VERSAO`.
3. Rode `python3 embutir.py`.

O passo 3 limpa, embute, propaga a versão para o `sw.js` e **recusa
publicar** se o conteúdo mudou e a letra não — ele guarda o SHA-256 da
última publicação em `publicado.json` e compara. Mudança só de
comentário não conta, porque não altera o publicado.

---

## Versões

O **script**, o **layout de bits** e o **cache do app** têm numeração
separada.

O script está na **1.0.12**; o `LAYOUT_VER` está em **6** desde que as
SPVARs 61-63 deixaram de guardar o MOD 21 e passaram a guardar a
permutação. Incremente o `LAYOUT_VER` apenas quando um campo mudar de
posição ou tamanho — e, ao fazer isso, atualize o app junto. App e
script divergindo em silêncio é o único jeito deste sistema falhar sem
dar sinal.

### 1.0.10 — validada em hardware (06/10/2026)

Compilada nos quatro scripts com **0 erros e 0 avisos**, e aprovada no
Cronus: deletar e reordenar MODs no aparelho sobrevivem ao
desligamento, que era o último defeito conhecido.

| | binário | % do limite |
|---|---|---|
| InLoco | 52.032 | 79,42% |
| Cities Skylines | 52.336 | 79,88% |
| Football-FIFA-eFoot | 52.400 | 79,98% |
| Mad Max | 52.656 | 80,37% |

`Variable slots` 481/1024 (47,16%) e `peak stack` 512/1024 (50,00%) em
todos — são as globais, que não dependem do jogo.

### 1.0.11 — o nome dos domínios (06/10/2026)

Os quatro domínios eram `D1`..`D4` no OLED, e nada mais. Quem usa dois ou três
contextos no mesmo jogo não lembra qual é qual — "a pé" e "no veículo" não cabem
num rótulo que diz `D2`.

O app ganhou um campo de nome por domínio, de **9 caracteres** (o que cabe na
linha do OLED ao lado do rótulo), saneado igual ao nome do jogo: sem `"`, sem `\`
e sem `//`, que quebrariam a `const string` gerada.

O que isto revelou, e é o motivo de a mudança valer o parágrafo: o gerador tem
**duas vias** — o `scriptCompleto()`, do botão de baixar, e o `codigo()`, do
"colar à mão". A segunda ainda emitia `GAME_NAME_3` e `GAME_NAME_4`, que **não
existem no script desde a 1.0b**, e emitia os `MODE_S` como `"D1".."D4"`,
divergindo da primeira. Quem seguisse a instrução colava duas linhas sem destino.
Duas vias para o mesmo dado é defeito esperando a hora; o portão passou a conferir
as duas (`testa_dom.js`).

### 1.0.12 — a auditoria (06/10/2026)

Uma varredura do app e do script inteiros, antes de ir a público. Oito defeitos,
três deles com consequência real:

1. **`THR_OUT = 100` gravava uma janela diferente da escolhida.** O empacotamento
   é `a*R+b`, e o operando limitado pelo rádix é o **b**. Com `THR_IN = 5` e
   `THR_OUT = 100`, `5*20+20 = 120` transbordava o campo e o aparelho lia
   `THR_IN = 30, THR_OUT = OFF`. O app mostrava uma coisa e o Cronus fazia outra —
   a forma de falha mais cara que este projeto tem.
2. **A seta de descer no MOD_20 corrompia a biblioteca.** `trocaMod(19,20)`
   lançava exceção no meio da troca e deixava `mods.length = 21` com
   `mods[19] = undefined`.
3. **O importador do backup não passava por nenhuma das sete normalizações** que
   o carregamento normal aplica. Um JSON de uma versão anterior entrava cru.

Cada um foi **reproduzido antes de consertar** — rodando o código, não lendo —
e reprovado de novo depois do conserto.

Entrou também o que a auditoria achou de acessibilidade, que num app usado no
celular com o controle na outra mão não é conformidade e sim configuração errada
gravada no Cronus: o botão de voltar e as setas de reordenar tinham ~29x33 px
contra os 44 px da diretriz; o `<select>` da cor do LED e o `<textarea>` do backup
não tinham nome acessível nenhum; e as cores de domínio na lista de jogos eram o
**único** canal da informação — invisíveis a leitor de tela e indistinguíveis em
várias formas de daltonismo.

Duas coisas que a auditoria ensinou sobre os próprios testes:

- **O molde que não consegue reprovar não prova nada.** A verificação de função
  órfã passava num script sabotado, porque o jogo do molde (Mad Max) é justamente
  o que usa todos os recursos. Precisou de um molde de **jogo vazio** para
  conseguir reprovar.
- **O nome acessível é calculado na árvore de acessibilidade, não no texto-fonte.**
  Meu verificador aceitava o `textContent` de um `<select>` como nome — e o
  `textContent` de um `<select>` são as suas *opções*. Tirar o `aria-label` da cor
  do LED passava. Só a sabotagem mostrou.

O portão foi de 12 para **15 verificações** — e para 16 com a verificação de que o README não contradiz o código, que entrou junto da documentação pública.

### O molde do portão virou sintético (06/10/2026)

O molde era o **Mad Max**, tirado da biblioteca do Daniel. Funcionava, e indo a público
trazia dois problemas. O menor é que configuração de jogo dele não é projeto — e o GitHub
Pages serve tudo o que está no repositório como arquivo publicamente legível.

O maior é que **ninguém sabia por que cada MOD daquele estava ali**. Molde herdado de um
jogo real cobre o que aquele jogo precisava, não o que o portão precisa verificar. A
cobertura era coincidência — e coincidência não se mantém: bastava o Daniel reconfigurar
o Mad Max para o portão passar a verificar outra coisa, sem avisar.

O `gera_molde.py` troca o dado achado por um dado **projetado**. Cada um dos 20 MODs tem
escrito ao lado o motivo de existir, e no fim o script **conta a cobertura** — 34 itens —
e reprova se perder um. As quatro sabotagens que fiz nele (alterar o TURBO medido, tirar o
BLOK, tirar o PASSIVO, zerar TURBO_MODO e CICLOS) reprovaram todas, nomeando o item.

O MOD_11 é declarado **intocável**: `tmp=[4,4,4,5]`, `lat=5`, 2CLK no CROSS. É o único
número do projeto medido no PLOT do Device Monitor com o Cronus na mão (149,8/50,1 ms
contra 150/50 configurados). Mexer nele cega a única ponte entre o simulador e o aparelho.

**Três defeitos que a troca de molde revelou**, e é por isso que ela valeu:

1. **O `testa_a11y.js` procurava o jogo por nome** — `findIndex(x => x.nome === 'Mad Max')`
   — e o MOD por índice fixo (`md = 6`). Trocar o molde o derrubou com
   `Cannot read properties of undefined`. Teste que depende do **nome do dado** não testa
   o app, testa o dado. Agora pega o primeiro jogo e, dentro dele, o MOD com mais campos
   de GAMA preenchidos, e reprova se o melhor tiver menos de dois.
2. **O teste de deletar aprovava vazio.** "Nenhum slot divergiu" é verdade também quando
   nenhum slot tem relação: um molde sem ZETA passava sem exercitar uma linha da
   permutação. O teste de *reordenar* já tinha essa guarda (`len(mexeu) >= 2`); o de
   deletar não, e a diferença só ficou visível ao trocar de molde. Provado com um molde
   sem nenhuma relação, que agora reprova nos dois.
3. **O tripwire do hash distinguiu certo**, e isso é notícia boa: o hash do **avulso**
   ficou inalterado e só o do **configurado** mudou. Ou seja, o script não mudou; o molde
   mudou. Era exatamente o que tinha de acontecer, e a linha de base nova foi registrada
   de propósito.

A verificação 17 fecha o círculo: o portão **regenera o molde e compara** com o
`sim_cfg.json`. Molde editado à mão mantém a aparência e perde a cobertura em silêncio —
provado tirando um `gHoldM`, mudança mínima e plausível, que reprovou.

O `sim_cfg_vazio.json` continua existindo e continua sendo necessário: **ele** é o molde
que *consegue* reprovar na verificação de função órfã. O sintético nunca reprovaria ali,
porque usa todos os recursos — e molde que não consegue reprovar não prova nada.

### O que continua em aberto, e não impede nada

1. **Por que a VM rodou a 16,1 ms numa sessão de 27/09.** Não se sabe,
   não é reproduzível, e o script não mede a própria velocidade. O
   sintoma e como conferir estão na seção do relógio.
2. **O app não absorve o que se faz no aparelho.** O `.znbk` carrega as
   SPVARs e o `decodifica.py` prova que sabe lê-las; um importador
   tornaria "regrave pelo app" em "traga o que você fez". É
   funcionalidade que não existe, não defeito.
3. **O teto de 20 MODs.** A EEPROM fecha em 64 de 64 palavras. Os 5 bits
   do selo (encurtar o hash de 29 para 24 bits) são a **única reserva**
   de memória persistente que resta — e ficam reservados de propósito,
   porque foi fechar a EEPROM sem ninguém decidir que fecharia que
   deixou o ZETA sem casa em primeiro lugar.

### Antes de mexer em qualquer coisa

```
python3 ferramentas/embutir.py
```

Ele audita a estrutura **e** roda o portão de comportamento: 17
verificações, cada uma conferida contra uma sabotagem deliberada. Se
fechar, não publicou nada.
