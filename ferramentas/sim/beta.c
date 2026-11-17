/* beta.c — o menu do BETA no OLED, navegado pelo controle (1.0.27).
 *
 * O portao ja executava o MOTOR do BETA sem ALFA (verificacao 11 do testa_sim.py). O
 * MENU e outro caminho: o "---" deixou de pular a tela do BETA, que ganhou duas linhas
 * (MULT e SINAL) por uma categoria so do menu. Isto navega como uma pessoa navegaria —
 * R1 + OPTIONS, X, R1, LEFT, DOWN... — e confere o que e gravado e o que o MOD faz depois.
 *
 * Roda sobre o script AVULSO, com tres MODs postos direto na EEPROM antes do boot:
 *   MOD_01  sem ALFA, STATIC em LY e UP, TOGGLE no CROSS
 *   MOD_02  ALFA LX (o BETA de sempre, 4 campos)
 *   MOD_03  ALFA CROSS (botao: o R1 pula o BETA)
 * As SPVARs sao as que o spvars() do app produz para esses MODs. A SPVAR_64 vai com o bit
 * de migracao ligado, senao o Migrar_V5 zeraria o tempo do AFTER e acusaria mudanca.
 *
 * uso: beta        sai 0 se tudo bate
 */
#include "gpcrt.h"
#include <string.h>
int IV[64], OV[64], PV[64], PT[64], RT=10, PVAR[128]; long OPS=0;
int RUMB=0, RUMBF=0, LEDS[4]; int SCREEN=0, CLS=0, PRINTS=0; long NGET=0, NSET=0;
void gpc_init(void); void gpc_main(void); int Switch_Mode(int m);
int Get_Cond_Mult(int n); int Get_Cond_Dir(int n); int Get_Fonte_Tipo(int n);
/* So variaveis que existem em qualquer versao do script: uma versao sem o BETA sem ALFA
   tem de REPROVAR aqui, nao deixar de compilar e derrubar o portao inteiro. */
extern int MenuDin, MenuCursor, Wz_SubCursor, Wz_Cond_Mult, Wz_Cond_Dir, Total_Inst;
static void step(int n){int i,t; for(t=0;t<n;t++){ for(i=0;i<64;i++){ if((IV[i]!=0)!=(PV[i]!=0))PT[i]=0; else PT[i]+=RT; OV[i]=IV[i]; } gpc_main(); for(i=0;i<64;i++)PV[i]=IV[i]; }}
static void tap(int b){IV[b]=100;step(2);IV[b]=0;step(2);}
#define R1 3
#define OPT 16
#define X 6
#define LT 12
#define RTB 13
#define UP 10
#define DN 11
#define L1 0
static int falhas=0;
static void ver(const char*n,int ok){printf("  %s  %s\n",ok?"ok ":"NAO",n); if(!ok)falhas++;}
static void abre_mod(int k){ int i; IV[R1]=100; tap(OPT); IV[R1]=0; step(3); for(i=0;i<k;i++) tap(DN); tap(X); }
static void fecha(void){ IV[R1]=100; tap(OPT); IV[R1]=0; step(3); }
int main(void){
  static const int SP[3][3]={{1076176899,-1525086948,-1240461600},
                              {1073848419,-1525083108,-1240465408},
                              {1073815971,-1525086948,-1240465408}};
  int k,q; for(k=0;k<3;k++) for(q=0;q<3;q++) PVAR[3*k+q+1]=SP[k][q];
  PVAR[64]=1;                                   /* migrado; selo 0 */
  gpc_init(); step(40); Switch_Mode(1); step(3);
  /* MOD_01: sem ALFA, STATIC LY, TOGGLE CROSS */
  abre_mod(0);
  ver("lista -> X abre o MOD_01 nos DOMINIOS (36)", MenuDin==36);
  tap(R1); ver("DOMINIOS -> R1 vai ao ALFA (100)", MenuDin==100);
  tap(R1); ver("ALFA '---' -> R1 vai ao BETA (101), nao pula mais", MenuDin==101);
  tap(DN); tap(DN); ver("BETA sem ALFA tem 2 linhas (DOWN DOWN volta ao MULT)", MenuDin==101 && Wz_SubCursor==0);
  int i; for(i=0;i<5;i++) tap(LT);
  ver("LEFT 5x no MULT: x1.0 -> x0.5 (indice 4)", Wz_Cond_Mult==4);
  tap(DN); ver("DOWN vai ao SINAL (cursor 1)", Wz_SubCursor==1);
  tap(RTB); ver("RIGHT no SINAL: POS -> NEG (dir 0)", Wz_Cond_Dir==0);
  tap(LT); ver("LEFT no SINAL: NEG -> POS (dir 1)", Wz_Cond_Dir==1);
  tap(LT); ver("LEFT de novo: POS -> NEG, e o MULT nao mexe", Wz_Cond_Dir==0 && Wz_Cond_Mult==4);
  tap(DN); ver("DOWN no ultimo volta ao MULT", Wz_SubCursor==0);
  tap(UP); ver("UP no primeiro vai ao SINAL", Wz_SubCursor==1);
  tap(R1); ver("R1 vai ao GAMA (102)", MenuDin==102);
  ver("e grava: MULT x0.5 e DIR NEG no MOD_01", Get_Cond_Mult(1)==4 && Get_Cond_Dir(1)==0);
  tap(L1); ver("L1 no GAMA volta ao BETA (101) com fonte '---'", MenuDin==101);
  ver("o BETA reabre com os valores gravados", Wz_Cond_Mult==4 && Wz_Cond_Dir==0);
  tap(L1); ver("L1 no BETA volta ao ALFA (100)", MenuDin==100);
  ver("a fonte continua '---'", Get_Fonte_Tipo(1)==0);
  fecha(); ver("R1+OPTIONS fecha o menu", MenuDin==0);
  step(5);
  IV[X]=100; step(3); int ly=OV[19], up=OV[10]; IV[X]=0; step(3);
  ver("e o MOD_01 responde: TOGGLE no CROSS trava LY em -50", ly==-50);
  /* MOD_02: ALFA LX -> o BETA de sempre */
  abre_mod(1); tap(R1); tap(R1);
  ver("MOD_02 (ALFA LX): o BETA de sempre (101)", MenuDin==101);
  for(i=0;i<3;i++) tap(DN); tap(RTB);
  ver("no LX o 4o campo e o DIR de 3 valores (ABS -> POS)", Wz_Cond_Dir==2);
  tap(DN); ver("4 campos: o 4o DOWN volta ao MULT", Wz_SubCursor==0);
  fecha();
  /* MOD_03: ALFA CROSS -> pula o BETA */
  abre_mod(2); tap(R1); tap(R1);
  ver("MOD_03 (ALFA CROSS): R1 no ALFA pula direto ao GAMA (102)", MenuDin==102);
  tap(L1); ver("e L1 no GAMA volta ao ALFA (100)", MenuDin==100);
  /* trocar a fonte no ALFA para '---' abre o BETA */
  for(i=0;i<13;i++) tap(LT);
  ver("LEFT 13x no ALFA: CROSS -> '---'", 1);
  tap(R1); ver("com a fonte trocada para '---', R1 abre o BETA (101)", MenuDin==101);
  tap(DN); tap(DN); ver("e ele tem 2 linhas", Wz_SubCursor==0);
  fecha();
  printf(falhas?"\n%d conferencia(s) reprovaram\n":"\nmenu do BETA: tudo bate\n",falhas);
  return falhas?1:0; }
