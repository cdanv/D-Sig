# D-Sig

Roteador de sinais para Cronus Zen (PS5), com aplicativo web para
catalogar as configurações e gerar o script pronto.

- **`index.html`** — o app. Contém o D-Sig embutido.
- **`D-Sig.gpc`** — o script avulso, se você quiser só ele.

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

**Só existe um app: o `index.html`.**

O `D-Sig.gpc` desta pasta e o template embutido no `index.html` são o
mesmo arquivo, byte a byte. Ao atualizar um, atualize o outro —
divergência entre os dois gera scripts inconsistentes sem dar nenhum
sinal.

Quem faz isso é o `embutir.py`: ele copia o `.gpc` para dentro do
`index.html` e compara os dois por SHA-256, falhando se divergirem.
Rode-o sempre que mexer no script.

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

1. Mexa no `D-Sig.gpc`.
2. Rode `python3 embutir.py` — ele embute e confere o SHA-256.
3. Em `sw.js`, incremente o número:

```js
const CACHE = 'dsig-v2';   // era dsig-v1
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
