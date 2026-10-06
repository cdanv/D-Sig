# D-Sig

**Roteador de sinais para Cronus Zen.** Um script GPC que recebe uma entrada do controle
e a encaminha para até quatro saídas, com condição, gatilho, tempo e relação entre MODs —
mais um aplicativo web que cataloga as configurações, explica o que cada uma vai fazer e
gera o script pronto para o Zen Studio.

Depois de gravado, **os MODs se ajustam no próprio aparelho** — pelo OLED e pelo controle,
sem computador — e o que você mudar ali sobrevive ao desligamento.

👉 **[cdanv.github.io/D-Sig](https://cdanv.github.io/D-Sig/)** — o aplicativo

---

## Por que existe

Escrever GPC à mão para cada ideia funciona até a terceira. Depois começam os problemas
que não são de programação:

- **Dois MODs brigando pela mesma saída** e nenhum jeito de ver isso antes de jogar.
- **Mudar um tempo** exige abrir o script, achar a linha, recompilar e regravar.
- **Lembrar o que cada script faz** três meses depois.
- **Ajustar no sofá**, com o jogo rodando, sem o computador por perto.

O D-Sig resolve isso tratando cada ideia como um **MOD**: um objeto com fonte, condição,
gatilho, saídas e relações. São 20 MODs por script, cada um descrito em 96 bits que vivem
na EEPROM do Cronus — então o ajuste feito no aparelho **sobrevive ao desligamento**.

## O que você precisa

| | |
|---|---|
| **Cronus Zen** | com um DualSense (PS5). O script é escrito para esse par |
| **Zen Studio** | para compilar e gravar o script |
| **Um navegador** | o app é uma página só, funciona offline depois de aberta |

O app é um **PWA**: abra o link, use o "Adicionar à tela de início" do navegador e ele
passa a abrir como aplicativo, sem barra de endereço e sem internet.

## Começando

**1. Monte a configuração no app.** Crie um jogo, dê nome aos quatro domínios, e adicione
MODs. Cada MOD tem cinco seções:

| seção | o que define | exemplo |
|---|---|---|
| **ALFA** | a **fonte**: qual entrada o MOD observa | o analógico esquerdo |
| **BETA** | a **condição**: a partir de que valor ele conta como acionado | acima de 20% |
| **GAMA** | o **gatilho**: o que liga e desliga o MOD | dois cliques no CROSS |
| **DELTA** | a **saída**: para onde o sinal vai, e com que tempo | TURBO no CROSS, 150 ms |
| **ZETA** | a **relação** com os outros MODs | exclui o MOD_04, bloqueia o MOD_07 |

O app mostra, em português, o que a combinação vai fazer — e **avisa** quando as
configurações se atrapalham: dois MODs escrevendo no mesmo destino, alvo de ZETA que não
divide domínio com quem o aponta, cadeia de ASSOC fechada em círculo, gatilho que o
PASSIVO engole.

**2. Gere e grave.** "Gerar código" entrega o `.gpc` inteiro. Abra no Zen Studio, Build,
grave num dos slots. O Cronus comporta **5 scripts D-Sig** ao mesmo tempo.

**3. Ajuste no aparelho.** **R1 + OPTIONS** abre o menu no OLED. Dali se cria, edita,
reordena e apaga MOD sem computador — `UP`/`DOWN` navega, `LEFT`/`RIGHT` ajusta, `X`
confirma, `SHARE` por 1 s grava na EEPROM. A lista completa de comandos está dentro do
próprio app, na ajuda.

## Os quatro domínios

Cada script tem quatro **domínios** — conjuntos de MODs que ligam juntos. Um MOD pode
pertencer a vários ou a nenhum, e só um domínio fica ligado por vez:

| | |
|---|---|
| **L1** + duplo-clique no **L3** | D1 |
| **R1** + duplo-clique no **R3** | D2 |
| **L1** + segurar o **L3** | D3 |
| **R1** + segurar o **R3** | D4 |

O L1 (ou o R1) tem de estar pressionado durante a ação no analógico — é o comando que mais
se esquece. O mesmo comando, no domínio que já está ligado, desliga. O LED do Cronus muda
de cor e o OLED mostra o nome que você deu ao domínio.

Serve para separar contextos do mesmo jogo: a pé e no veículo, mira e movimentação,
combate e exploração.

## Limites, sem letra miúda

| | |
|---|---|
| MODs por script | **20** |
| Scripts D-Sig no Cronus | **5** |
| Destinos por MOD | **4** |
| Domínios | **4** |
| Nome do jogo no OLED | 20 caracteres |
| Nome de domínio no OLED | 9 caracteres |

**O que não sobrevive ao desligamento sem o app:** nada, desde a 1.0.10. Antes dela,
deletar ou reordenar MODs no aparelho perdia as relações ZETA no boot seguinte. Hoje uma
permutação gravada na EEPROM mantém tudo no lugar. A EEPROM fecha em **64 de 64
palavras** — 60 para os 20 MODs, 3 para a permutação, 1 para o selo.

## Estado

**Versão 1.0.12.** Validada em hardware: compila com 0 erros e 0 avisos nos quatro
scripts de referência, e os ajustes feitos no aparelho sobrevivem ao desligamento.

Cada publicação passa por um portão de **17 verificações** que executam o script num
simulador — entre elas os tempos do TURBO, que foram medidos no PLOT do Device Monitor com
o Cronus na mão e saíram iguais aos do simulador (150/50 ms configurados, 149,8/50,1 ms
medidos). Nenhuma dessas verificações foi aceita sem antes ser provada contra uma sabotagem
deliberada: um script quebrado de propósito tem de reprovar nela, senão a verificação não
está verificando nada.

### O que continua em aberto

1. **Numa sessão de setembro a VM do Cronus rodou a 16,1 ms por volta** em vez de 10 ms, e
   todos os tempos saíram 1,63× mais longos. Não é reproduzível e o script não pode medir
   a própria velocidade. Se os tempos saírem longos, confira a largura da rampa no PLOT do
   Device Monitor — rampa larga significa volta longa.
2. **O app não importa de volta o que você fez no aparelho.** O backup `.znbk` do Zen
   Studio contém as SPVARs; um importador tornaria "regrave pelo app" em "traga o que
   você fez". É funcionalidade que falta, não defeito.

## Para quem for mexer no código

| arquivo | o que é |
|---|---|
| `index.html` | o app, página única, com o script embutido como template |
| `D-Sig.gpc` | o script avulso, sem comentários, pronto para o Zen Studio |
| `ferramentas/D-Sig.fonte.gpc` | **o mesmo script, comentado.** É o arquivo que se edita |
| `ferramentas/embutir.py` | **a única ferramenta de publicação** |
| `ferramentas/testa_sim.py` | o portão: as 17 verificações, que **executam** o script |
| `ferramentas/sim/` | o simulador — transpila o GPC para C e roda os cenários |

```bash
cd ferramentas && python3 embutir.py
```

O `embutir.py` audita a estrutura e roda o portão de comportamento. **Se ele fechar, nada
foi publicado.** Precisa de `python3`, `gcc`, e `npm i -g jsdom playwright`.

Três regras que o projeto segue e que as auditorias impõem:

1. **O `D-Sig.gpc` publicado e o template dentro do `index.html` têm o mesmo SHA-256.** O
   app é a fonte única; o avulso é cópia.
2. **A versão nunca anda para trás.** Ela identifica a publicação, não o conteúdo.
3. **Teste que não consegue reprovar não prova nada.** Toda verificação do portão foi
   conferida contra um script deliberadamente quebrado.

O [`LEIAME.md`](LEIAME.md) é o diário de engenharia: a arquitetura, o layout de bits, as
medições, e cada decisão com o motivo e o que ela substituiu. É longo de propósito.

## Sobre o uso

O D-Sig é um **roteador de sinais e automatizador de sequências**: ele encaminha entradas
do seu controle para saídas, com tempo e condição. Não há nele nada de assistência de
mira, leitura de memória do jogo ou interação com o servidor.

O que você faz com isso é sua responsabilidade. Muitos jogos online proíbem entrada
automatizada nos termos de uso, e a punição é entre você e eles.

## Licença

**Ainda não definida.** Sem licença, o padrão legal é que ninguém pode copiar, modificar
ou redistribuir — o que provavelmente não é a intenção de publicar. Se o objetivo é que
outras pessoas usem e adaptem, convém escolher uma (MIT é a mais simples) e adicionar o
arquivo `LICENSE`.
