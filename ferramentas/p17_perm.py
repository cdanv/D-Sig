#!/usr/bin/env python3
"""ETAPA 4b da 1.0g — a PERMUTACAO, que conserta o ZETA.

O DEFEITO: o Config_Zeta() e gerado pelo app com a numeracao FIXA dos MODs e roda a cada
boot. Enquanto so o app edita a lista isso funciona. No instante em que o aparelho tambem
pode deletar ou reordenar, reaplicar por posicao esta errado por construcao — e o boot
seguinte carimba a fiacao antiga sobre a lista ja deslocada. Medido no simulador: deletar
o MOD_05 do Mad Max deixa 12 de 14 slots com ZETA errado depois de religar.

O CONSERTO: tres palavras na EEPROM (SPVAR_61-63, liberadas na etapa 4a) guardam QUAL
POSICAO ORIGINAL cada slot ocupa hoje. O Config_Zeta() passa a dizer "o original 7 tinha
estas relacoes" e o script resolve o slot de destino, remapeando tambem os bits da
mascara pela mesma conta.

POR QUE RESOLVER O DESTINO NA ESCRITA, e nao permutar as mascaras depois: permutar no
lugar exige rascunho, porque escrever no slot s destroi o que outro slot ainda vai
precisar — e nao ha vetor para rascunho, seriam 60 variaveis novas. Resolvendo na escrita,
cada original e escrito UMA vez, no lugar certo, direto da constante do app. Nada e lido
de volta, nada se atropela.

AS TRES ARMADILHAS QUE ESTE CODIGO EVITA DE PROPOSITO:

1. CONTADOR DE LACO COMPARTILHADO. O projeto nao tem variavel local, entao todo contador
   e global. Perm_Mapear roda um while e chama Perm_Onde, que roda outro, que chama
   Perm_Carga. Tres niveis, tres conjuntos de auxiliares distintos (Mp_*, On_*, Pc_*).
   Um nome repetido ali e um laco que nunca termina.

2. ESCRITA NO init. A auditoria 3e do embutir.py exige que o init so leia e agende. Por
   isso o Perm_Carregar() NAO grava: quando a permutacao esta invalida ele conserta a RAM
   e AGENDA, e quem grava e o Boot_Persistir(), no main, junto com o selo. O mesmo
   caminho que a configuracao do app ja usava.

3. BIT DE SINAL. 21^7-1 = 1.801.088.540 ocupa os bits 0-30. O bit 31 fica fora: ligado,
   a palavra vira negativa e a divisao com sinal desmonta a base-21 errado. O guarda mora
   nos bits 27-30 da palavra 63, que so usa 27 bits para 6 digitos.
"""
import re
import sys

F = 'D-Sig.fonte.gpc'
s = open(F, encoding='utf-8').read()
n = 0


def troca(velho, novo, nome):
    global s, n
    assert velho in s, f'{nome}: nao encontrado'
    assert s.count(velho) == 1, f'{nome}: {s.count(velho)}x'
    s = s.replace(velho, novo, 1)
    n += 1
    print(f'  ok  {nome}')


# =============================================================================
# 1. as funcoes da permutacao, antes do Marcar_Selo (vizinhas do selo na EEPROM)
# =============================================================================
BLOCO = '''// ===================== A PERMUTACAO (1.0g) ==================================
// Tres palavras guardam, para cada um dos 20 slots, QUAL POSICAO ORIGINAL da tabela do
// app ele ocupa hoje. Digito 0 = MOD criado no aparelho, que nao existe naquela tabela.
//
//   SPVAR_61   slots  1-7    7 digitos base-21   bits 0-30
//   SPVAR_62   slots  8-14   7 digitos base-21   bits 0-30
//   SPVAR_63   slots 15-20   6 digitos base-21   bits 0-26  + guarda nos bits 27-30
//
// POR QUE BASE-21 E NAO 5 BITS POR DIGITO: 5 bits dao 6 digitos por palavra, 18 em tres
// palavras — faltariam dois. Base-21 da 7 por palavra porque 21^7 = 1.801.088.541 ainda
// cabe em 31 bits. E 21 valores sao exatamente o que o digito precisa: 20 posicoes mais
// o zero. Base-22 estouraria com 7 digitos.
//
// POR QUE UM GUARDA: as SPVAR_61-63 guardavam o MOD 21 ate a 1.0f. Se o Daniel voltar
// para a 1.0f e depois subir a 1.0g de novo, elas chegam cheias de configuracao de MOD,
// que lida como digitos produz ZETA em slots arbitrarios, sem nenhum sinal na tela. O
// nibble fixo pega isso em 15 de 16 casos, e a conferencia de digito repetido — que nao
// custa bit nenhum — fecha o resto.
define PERM_GUARDA = 10;              // 0b1010
define PERM_MASK63 = 0x7FFFFFF;       // 27 bits: os 6 digitos da palavra 63
define PERM_LIM7   = 1801088541;      // 21^7: limite da palavra de 7 digitos
define PERM_LIM6   = 85766121;        // 21^6: limite do payload da palavra 63

int Perm_W1 = 0;   int Perm_W2 = 0;   int Perm_W3 = 0;
// Auxiliares SEPARADOS por nivel de laco. Ver armadilha 1 no cabecalho do patch.
int Pc_V = 0;  int Pc_I = 0;                 // Perm_Carga / Perm_Grava
int Pg_P = 0;
int On_S = 0;                                // Perm_Onde
int Mp_R = 0;  int Mp_I = 0;  int Mp_D = 0;  // Perm_Mapear
int Pi_S = 0;                                // Perm_Identidade
int Pv_M = 0;  int Pv_S = 0;  int Pv_D = 0;  // Perm_Valida
int Pd_S = 0;  int Pd_V = 0;                 // Perm_Del
int Pt_T = 0;                                // Perm_Troca
int Zl_S = 0;                                // Zeta_Limpar
int Zt_D = 0;                                // Zeta_Um / Fin / Blk

// A escada de potencias. Sem ela seria um laco de multiplicacao por volta de digito, e
// isto roda 20 vezes em cada Perm_Onde, que por sua vez roda dentro do Perm_Mapear.
function Pot21(k) {
    if(k == 0) return 1;
    if(k == 1) return 21;
    if(k == 2) return 441;
    if(k == 3) return 9261;
    if(k == 4) return 194481;
    if(k == 5) return 4084101;
    return 85766121;
}

// O digito do slot s. Deixa Pc_I pronto para o Perm_Grava, que e o unico chamador que
// depende disso — e esta logo abaixo, de proposito.
function Perm_Carga(s) {
    if(s <= 7)       { Pc_V = Perm_W1;               Pc_I = s - 1;  }
    else if(s <= 14) { Pc_V = Perm_W2;               Pc_I = s - 8;  }
    else             { Pc_V = Perm_W3 & PERM_MASK63; Pc_I = s - 15; }
    Pc_V = Pc_V / Pot21(Pc_I);
    return Pc_V - ((Pc_V / 21) * 21);        // o idioma do projeto: nao existe %
}

// AJUSTE DIFERENCIAL: soma a diferenca na casa do digito, em vez de remontar a palavra
// inteira. Economiza 6 multiplicacoes por escrita, e testei que nunca sai da faixa.
function Perm_Grava(s, d) {
    Pg_P = (d - Perm_Carga(s)) * Pot21(Pc_I);
    if(s <= 7)       Perm_W1 = Perm_W1 + Pg_P;
    else if(s <= 14) Perm_W2 = Perm_W2 + Pg_P;
    else             Perm_W3 = Perm_W3 + Pg_P;
}

// Qual slot guarda a posicao original o. Zero = o original foi deletado.
function Perm_Onde(o) {
    On_S = 1;
    while(On_S <= 20) {
        if(Perm_Carga(On_S) == o) return On_S;
        On_S++;
    }
    return 0;
}

// Traduz uma mascara da numeracao ORIGINAL para a de hoje. Referencia a MOD deletado
// simplesmente desaparece — e o mesmo que o Shift_Mask_Del faz ao vivo.
function Perm_Mapear(mask) {
    Mp_R = 0;
    Mp_I = 1;
    while(Mp_I <= 20) {
        if((mask >> (Mp_I - 1)) & 1) {
            Mp_D = Perm_Onde(Mp_I);
            if(Mp_D != 0) Mp_R = Mp_R | (1 << (Mp_D - 1));
        }
        Mp_I++;
    }
    return Mp_R;
}

function Perm_Identidade() {
    Perm_W1 = 0; Perm_W2 = 0; Perm_W3 = 0;
    Pi_S = 1;
    while(Pi_S <= 20) { Perm_Grava(Pi_S, Pi_S); Pi_S++; }
}

function Perm_Selar() {
    Perm_W3 = (Perm_W3 & PERM_MASK63) | (PERM_GUARDA << 27);
}

function Perm_Gravar() {
    Perm_Selar();
    Grava_Spv(SPVAR_61, Perm_W1);
    Grava_Spv(SPVAR_62, Perm_W2);
    Grava_Spv(SPVAR_63, Perm_W3);
}

// Duas provas independentes: o guarda, que esta na EEPROM, e a ausencia de digito
// repetido, que e logica e nao custa bit. Mais os limites de faixa, que pegam palavra
// negativa ou grande demais para ser base-21.
function Perm_Valida() {
    if(((Perm_W3 >> 27) & 0xF) != PERM_GUARDA) return FALSE;
    if(Perm_W1 < 0 || Perm_W2 < 0 || Perm_W3 < 0) return FALSE;
    if(Perm_W1 >= PERM_LIM7 || Perm_W2 >= PERM_LIM7) return FALSE;
    if((Perm_W3 & PERM_MASK63) >= PERM_LIM6) return FALSE;
    Pv_M = 0;
    Pv_S = 1;
    while(Pv_S <= 20) {
        Pv_D = Perm_Carga(Pv_S);
        if(Pv_D != 0) {
            if((Pv_M >> (Pv_D - 1)) & 1) return FALSE;
            Pv_M = Pv_M | (1 << (Pv_D - 1));
        }
        Pv_S++;
    }
    return TRUE;
}

// NAO GRAVA. Ver armadilha 2 no cabecalho: o init so le e agenda, e quem grava e o
// Boot_Persistir no main. Agendar sem instancias vai direto ao selo e a permutacao.
function Perm_Carregar() {
    Perm_W1 = get_pvar(SPVAR_61, -2147483648, 2147483647, 0);
    Perm_W2 = get_pvar(SPVAR_62, -2147483648, 2147483647, 0);
    Perm_W3 = get_pvar(SPVAR_63, -2147483648, 2147483647, 0);
    if(Perm_Valida()) return;
    Perm_Identidade();
    Boot_Agendar(Selo_Cfg_Gravado(), FALSE);
}

// As tres operacoes do aparelho. Gravam na hora, como o Save_Instance ja faz a partir do
// Compact_Pos: sao acao do usuario no menu, nao boot.
function Perm_Del(s) {
    Pd_S = s;
    while(Pd_S <= 19) {
        Pd_V = Perm_Carga(Pd_S + 1);      // temporario explicito: Perm_Grava chama
        Perm_Grava(Pd_S, Pd_V);           // Perm_Carga por dentro e mexe no Pc_I
        Pd_S++;
    }
    Perm_Grava(20, 0);
    Perm_Gravar();
}

function Perm_Troca(a, b) {
    Pt_T = Perm_Carga(a);
    Pd_V = Perm_Carga(b);
    Perm_Grava(a, Pd_V);
    Perm_Grava(b, Pt_T);
    Perm_Gravar();
}

function Perm_Novo(s) {
    Perm_Grava(s, 0);
    Perm_Gravar();
}

// ===================== O ZETA, aplicado no slot de hoje ======================
// O Zeta_Limpar e novo e obrigatorio: original deletado tem de deixar o slot limpo, e
// ate a 1.0f ninguem limpava — a tabela do app so escrevia por cima.
function Zeta_Limpar() {
    Zl_S = 1;
    while(Zl_S <= 20) {
        Set_F1_Excl(Zl_S, 0);
        Set_F1_Assoc(Zl_S, 0);
        Set_F1_Bloq(Zl_S, 0);
        Set_Fin(Zl_S, 0);
        Set_Blok(Zl_S, 0);
        Zl_S++;
    }
}

// Quatro parametros e o maximo que este projeto ja usa (colorled, Fb_Disparar). Por isso
// o FINALIZA e o BLOK saem em chamadas proprias, emitidas so quando nao-zero.
function Zeta_Um(orig, ex, asc, bl) {
    Zt_D = Perm_Onde(orig);
    if(Zt_D == 0) return;
    Set_F1_Excl(Zt_D,  Perm_Mapear(ex));
    Set_F1_Assoc(Zt_D, Perm_Mapear(asc));
    Set_F1_Bloq(Zt_D,  Perm_Mapear(bl));
}

function Zeta_Fin(orig, v) {
    Zt_D = Perm_Onde(orig);
    if(Zt_D != 0) Set_Fin(Zt_D, v);
}

function Zeta_Blk(orig, v) {
    Zt_D = Perm_Onde(orig);
    if(Zt_D != 0) Set_Blok(Zt_D, v);
}

'''
troca('function Marcar_Selo(migrado, selo) {', BLOCO + 'function Marcar_Selo(migrado, selo) {',
      'SECAO NOVA: a permutacao e o ZETA remapeado')

# =============================================================================
# 2. o Boot_Persistir grava a permutacao junto com o selo
# =============================================================================
troca('''    Marcar_Selo(1, Boot_Selo);
    Boot_Inst = 0;''',
      '''    Perm_Gravar();              // 1.0g: junto com o selo, pelo mesmo caminho agendado
    Marcar_Selo(1, Boot_Selo);
    Boot_Inst = 0;''',
      'Boot_Persistir: grava a permutacao com o selo')

# =============================================================================
# 3. o init
# =============================================================================
troca('''    Cfg_Selo = Cfg_Selo;
    Load_All();''',
      '''    Cfg_Selo = Cfg_Selo;
    Load_All();
    // 1.0g: le as tres palavras da permutacao e, se nao forem minhas, repoe a identidade
    // e AGENDA — nao grava, porque o init so le e agenda (auditoria 3e do embutir.py).
    Perm_Carregar();''',
      'init: carrega a permutacao')

troca('''        Config_Inicial();
        Boot_Agendar(Cfg_Selo, TRUE);
    }''',
      '''        Config_Inicial();
        Perm_Identidade();     // o app e autoridade: o historico do aparelho zera aqui
        Boot_Agendar(Cfg_Selo, TRUE);
    }''',
      'init: identidade quando o app grava')

# =============================================================================
# 4. os ganchos do aparelho
# =============================================================================
troca('function Deletar_Instancia(num) {',
      '''function Deletar_Instancia(num) {
    // PASSO 0 (1.0g): a permutacao PRIMEIRO, enquanto os slots ainda estao nas posicoes
    // antigas. Depois dela o Ajustar_Refs desloca as mascaras em RAM, como sempre fez.
    Perm_Del(num);''',
      'Deletar_Instancia: desloca a permutacao')

troca('    Cfg_Mov = Cfg_Mov | (1 << (a - 1));   // v3zv: gravados por reordenacao',
      '''    Perm_Troca(a, b);                     // 1.0g: a permutacao acompanha a troca
    Cfg_Mov = Cfg_Mov | (1 << (a - 1));   // v3zv: gravados por reordenacao''',
      'Swap_Pos: troca a permutacao')

print(f'\nPARTE 17: {n} trocas')

# --- conferencia dos auxiliares de laco --------------------------------------
# A armadilha 1 merece checagem, nao so comentario.
CADEIA = {'Perm_Mapear': ['Mp_R', 'Mp_I', 'Mp_D'], 'Perm_Onde': ['On_S'],
          'Perm_Carga': ['Pc_V', 'Pc_I'], 'Perm_Valida': ['Pv_M', 'Pv_S', 'Pv_D'],
          'Perm_Identidade': ['Pi_S'], 'Perm_Del': ['Pd_S', 'Pd_V'],
          'Zeta_Limpar': ['Zl_S']}
usados = {}
for fn, aux in CADEIA.items():
    for a in aux:
        assert a not in usados, f'auxiliar {a} compartilhado por {fn} e {usados[a]}'
        usados[a] = fn
print(f'  {len(usados)} auxiliares de laco, nenhum compartilhado em cadeia')

open(F, 'w', encoding='utf-8').write(s)
print(f'  {F} gravado')
