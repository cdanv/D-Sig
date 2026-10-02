/* zeta.c — reproduz, em software, o bug do ZETA que nao acompanha o deslocamento.
 *
 * O QUE SE QUER PROVAR: deletar um MOD pelo OLED acerta as mascaras ZETA em RAM, mas o
 * Config_Zeta() do app reaplica a tabela POR POSICAO FIXA a cada boot — entao depois de
 * desligar e ligar, cada relacao aponta para o MOD errado. Foi o que o Daniel observou.
 *
 * COMO SE SIMULA O DESLIGAMENTO: nao dá para chamar gpc_init() duas vezes no mesmo
 * processo — as variaveis globais do script sobreviveriam, e e exatamente a morte delas
 * que caracteriza o desligamento. Entao sao DOIS processos:
 *
 *   fase A  PVAR zerado -> boot -> deleta o MOD pelo menu -> imprime -> grava PVAR
 *   fase B  carrega PVAR -> boot -> imprime
 *
 * A EEPROM (PVAR) atravessa; tudo o mais nasce de novo. E um ciclo de energia de verdade.
 *
 * uso: zeta A <slot> <arquivo_eeprom>
 *      zeta B <arquivo_eeprom>
 */
#include "gpcrt.h"
#include <string.h>
int IV[64], OV[64], PV[64], PT[64], RT=10, PVAR[128]; long OPS=0;
int RUMB=0, RUMBF=0, LEDS[4];
int SCREEN=0, CLS=0, PRINTS=0;
long NGET=0, NSET=0;
void gpc_init(void); void gpc_main(void); int Switch_Mode(int m);
int Get_F1_Excl(int n); int Get_F1_Assoc(int n); int Get_F1_Bloq(int n);
extern int Total_Inst, MenuDin, MenuCursor;

#define L2 1
#define R1 3
#define X  6
#define TRI 9
#define DN 11
#define OPT 16

static void step(int n){int i,t; for(t=0;t<n;t++){
  for(i=0;i<64;i++){ if((IV[i]!=0)!=(PV[i]!=0))PT[i]=0; else PT[i]+=RT; OV[i]=IV[i]; }
  gpc_main();
  for(i=0;i<64;i++)PV[i]=IV[i]; }}
static void tap(int b){IV[b]=1;step(2);IV[b]=0;step(2);}

static void imprime(const char *rot){
  int n;
  for(n=1;n<=21;n++){
    int e=Get_F1_Excl(n), a=Get_F1_Assoc(n), b=Get_F1_Bloq(n);
    if(e||a||b) printf("%s slot=%02d excl=%d assoc=%d bloq=%d\n", rot, n, e, a, b);
  }
  printf("%s TOTAL=%d\n", rot, Total_Inst);
}

int main(int argc, char **argv){
  if(argc<3){ fprintf(stderr,"uso: zeta A <slot> <eeprom> | zeta B <eeprom> | zeta C <a> <b> <eeprom>\n"); return 2; }

  if(argv[1][0]=='B'){
    FILE *f=fopen(argv[2],"rb");
    if(!f){ fprintf(stderr,"nao abriu %s\n",argv[2]); return 2; }
    if(fread(PVAR,sizeof(int),128,f)!=128){ fclose(f); fprintf(stderr,"eeprom curta\n"); return 2; }
    fclose(f);
    gpc_init(); step(3); Switch_Mode(1); step(30);
    imprime("reboot");
    return 0;
  }

  if(argv[1][0]=='C'){                     /* reordenar: troca dois slots */
    int a=atoi(argv[2]), b=atoi(argv[3]); const char *arq=argv[4];
    memset(PVAR,0,sizeof(PVAR));
    gpc_init(); step(3); Switch_Mode(1); step(30);
    imprime("antes");
    IV[R1]=1; tap(OPT); IV[R1]=0; step(3);
    if(MenuDin!=1){ fprintf(stderr,"ERRO: a lista nao abriu\n"); return 3; }
    int k;
    for(k=1;k<a;k++) tap(DN);              /* cursor ate o slot a */
    IV[L2]=1;                              /* L2 + BAIXO move o MOD, nao o cursor */
    for(k=a;k<b;k++) tap(DN);
    IV[L2]=0; step(5);
    imprime("depois");
    FILE *f=fopen(arq,"wb"); if(!f) return 2;
    fwrite(PVAR,sizeof(int),128,f); fclose(f); return 0;
  }

  int alvo = atoi(argv[2]);
  const char *arq = argv[3];
  memset(PVAR,0,sizeof(PVAR));            /* Cronus limpo */
  gpc_init(); step(3); Switch_Mode(1); step(30);   /* 30 voltas: o Boot_Persistir termina */
  imprime("antes");

  /* abre a lista: R1 + OPTIONS */
  IV[R1]=1; tap(OPT); IV[R1]=0; step(3);
  if(MenuDin!=1){ fprintf(stderr,"ERRO: a lista nao abriu (MenuDin=%d)\n",MenuDin); return 3; }

  /* desce o cursor ate o slot alvo */
  int k;
  for(k=1;k<alvo;k++) tap(DN);
  if(MenuCursor!=alvo-1){ fprintf(stderr,"ERRO: cursor em %d, esperado %d\n",MenuCursor,alvo-1); return 3; }

  /* segura TRIANGLE ate o DELETAR? */
  IV[TRI]=1;
  for(k=0;k<300 && MenuDin!=38;k++) step(1);
  IV[TRI]=0; step(2);
  if(MenuDin!=38){ fprintf(stderr,"ERRO: o DELETAR? nao apareceu\n"); return 3; }

  /* confirma com X */
  tap(X); step(40);
  if(MenuDin!=1){ fprintf(stderr,"AVISO: MenuDin=%d apos o X\n",MenuDin); }
  imprime("depois");

  FILE *f=fopen(arq,"wb");
  if(!f){ fprintf(stderr,"nao gravou %s\n",arq); return 2; }
  fwrite(PVAR,sizeof(int),128,f); fclose(f);
  return 0;
}
