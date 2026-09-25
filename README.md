# D-Sig

Roteador de sinais para Cronus Zen (PS5), com aplicativo web para
catalogar as configurações e gerar o script pronto.

- **`index.html`** — o app. Contém o D-Sig embutido.
- **`D-Sig.gpc`** — o script avulso, limpo, pronto para o ZenStudio.
- **`D-Sig.fonte.gpc`** — o mesmo script comentado. É o arquivo que se
  edita, e onde está explicado o *porquê* de cada decisão.

O que o **GitHub Pages** precisa servir são `index.html`, `manifest.json`,
`sw.js` e os três ícones. O resto fica no repositório sem atrapalhar, e é
onde convém guardá-lo — o `.gpc` avulso só tem valor se estiver ao lado do
`index.html` de que ele é cópia.

### As ferramentas

| arquivo | o que faz |
|---|---|
| `embutir.py` | **a única ferramenta de publicação.** Limpa, publica, embute, propaga a versão e recusa entregar algo errado |
| `limpar.py` | o removedor de comentários e a lista das 7 âncoras que o app usa |
| `publicado.json` | o SHA-256 da última publicação. É com ele que o `embutir.py` recusa publicar conteúdo novo sob a mesma letra de build |
| `oled/padrao.py` | **a fonte única da arte do OLED.** Dele saem os PNGs de revisão, o `timbre.png` e o código das telas |
| `oled/png2gpc.py` | PNG de 1 bit → `const image` do GPC, no formato que o compilador exige |

A cadeia da arte é reproduzível a partir do repositório: `python3 oled/padrao.py`
grava o `timbre.png`, e o `oled/png2gpc.py` devolve deste os mesmos 300 bytes
que estão no `const image DS_TIMBRE` do publicado.

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
- faltar uma das 7 âncoras de texto que o app usa para injetar a
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

Cada MOD ocupa **3 SPVARs** de 32 bits — 96 bits, todos em uso. Com 21
MODs isso são 63 das 64 SPVARs.

A **SPVAR_64** não está livre: o bit 0 marca que a migração de layout já
foi feita, e os bits 1–31 guardam o selo da configuração gerada pelo app.
Cada um tem seu espaço para que um não apague o outro.

### Gravação: nunca no `init`

A EEPROM do Cronus é frágil — a documentação a descreve como *rated for
1000's of* ciclos de leitura/gravação — e gravar nela é lento. Duas
regras, as duas nascidas de uma pane real:

1. **O `init` não grava.** Ele só lê e **agenda**. Quem grava é o
   `Boot_Persistir`, na primeira linha do `main`: uma instância (3
   SPVARs) por volta, e o selo no fim. As 21 levam ~210 ms.
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
| EEPROM zerada, app com 21 MODs | 128 | 64, em 21 voltas |
| migração de layout antigo | 64 | **4** |
| regerar script com 1 MOD alterado | 64 | **2** |
| boot normal | 0 | 0 |
| **pico numa só passagem** | **128** | **3** |

Precisando espaçar ainda mais, o passo a dividir é o `Boot_Persistir`:
um SPVAR por volta em vez de três levaria 63 voltas (~630 ms) e exigiria
um dispatch por SPVAR.

O `Salvar_Tudo`, que gravava as 21 de uma vez, deixou de existir — era
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

## Versionamento e publicação

A versão vive em **um lugar só**, no `D-Sig.fonte.gpc`:

```gpc
const string DS_VERSAO    = "D-Sig 1.0b";
```

O número é a versão do **script**; a letra é o **build**, e ela muda em
toda publicação. Dessa string saem, automaticamente:

- o que aparece no **OLED**, no menu de status (OPTIONS);
- o título e a tela de Informações do **app**, que lê a string do próprio
  template embutido;
- o nome do cache do service worker (`dsig-1.0b`).

Assim os três nunca discordam. Se o OLED diz `1.0b` e o app diz `1.0c`,
o Cronus está com uma versão anterior gravada — e a resposta é olhar a
tela, não abrir arquivo.

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

O script está na **1.0b**; o `LAYOUT_VER` está em **5**, porque as
posições dos campos nos SPVARs não mudam desde então. Incremente o
`LAYOUT_VER` apenas quando um campo mudar de posição ou tamanho — e,
ao fazer isso, atualize o app junto. App e script divergindo em
silêncio é o único jeito deste sistema falhar sem dar sinal.
