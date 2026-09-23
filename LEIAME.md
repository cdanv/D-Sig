# D-Sig

Roteador de sinais para Cronus Zen (PS5), com aplicativo web para
catalogar as configurações e gerar o script pronto.

- **`index.html`** — o app. Contém o D-Sig embutido.
- **`D-Sig.gpc`** — o script avulso, limpo, pronto para o ZenStudio.
- **`D-Sig.fonte.gpc`** — o mesmo script comentado. É o arquivo que se
  edita, e onde está explicado o *porquê* de cada decisão.

O que o GitHub Pages precisa servir são quatro arquivos — `index.html`,
`manifest.json`, `sw.js` e os três ícones. O `.gpc` e as ferramentas
(`embutir.py`, `verificar_gpc.py`) podem ficar no repositório sem
atrapalhar, e é onde convém guardá-los: o `.gpc` avulso só tem valor se
estiver ao lado do `index.html` de que ele é cópia.

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
- faltar uma das 9 âncoras de texto que o app usa para injetar a
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

O que isso resolveu: depois de uma **limpeza de slots no ZenStudio** a
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

## Publicando uma versão nova

1. Mexa no `D-Sig.fonte.gpc` — nunca no `D-Sig.gpc`.
2. Rode `python3 embutir.py`. Ele limpa, embute e confere tudo.
3. Em `sw.js`, incremente o número:

```js
const CACHE = 'dsig-v4';   // era dsig-v3
```

É essa troca que faz o navegador buscar a versão nova. Sem ela, quem
já tem o app instalado continua na anterior. Incremente **sempre** que
o `index.html` mudar, inclusive quando só o template embutido mudar.

---

## Versões

O **script**, o **layout de bits** e o **cache do app** têm numeração
separada.

O script está na **1.0**; o `LAYOUT_VER` está em **5**, porque as
posições dos campos nos SPVARs não mudam desde então. Incremente o
`LAYOUT_VER` apenas quando um campo mudar de posição ou tamanho — e,
ao fazer isso, atualize o app junto. App e script divergindo em
silêncio é o único jeito deste sistema falhar sem dar sinal.
