/* tri.c — quanto tempo de TRIANGLE a lista exige para abrir o DELETAR?
   O define diz TIME_TRI_DELETE = 1000 e o Daniel observou ~2 s. Em vez de discutir,
   medir: segura TRIANGLE e conta as voltas ate MenuDin virar 38. */
#include "gpcrt.h"
int IV[64], OV[64], PV[64], PT[64], RT=10, PVAR[128]; long OPS=0;
int RUMB=0, RUMBF=0, LEDS[4];
int SCREEN=0, CLS=0, PRINTS=0;
long NGET=0, NSET=0;
void gpc_init(void); void gpc_main(void); int Switch_Mode(int m);
extern int CurrentMode, MenuDin, MenuCursor, Total_Inst;
static int T=0;
static void step(int n){int i,t; for(t=0;t<n;t++){
  for(i=0;i<64;i++){ if((IV[i]!=0)!=(PV[i]!=0))PT[i]=0; else PT[i]+=RT; OV[i]=IV[i]; }
  gpc_main();
  for(i=0;i<64;i++)PV[i]=IV[i]; T+=RT; }}
#define R1 3
#define TRI 9
#define OPT 16
int main(void){
  gpc_init(); step(2); Switch_Mode(1); step(3);
  IV[R1]=1; IV[OPT]=1; step(2); IV[OPT]=0; step(2); IV[R1]=0; step(3);
  printf("menu aberto: MenuDin=%d  MODs=%d  cursor=%d\n", MenuDin, Total_Inst, MenuCursor);
  if(MenuDin!=1){ printf("ERRO: a lista nao abriu\n"); return 1; }
  int t0=T;
  IV[TRI]=1;
  int v;
  for(v=0; v<500; v++){
    step(1);
    if(MenuDin==38){ printf("DELETAR? apareceu com %d ms de TRIANGLE (%d voltas)\n",
                            T-t0, v+1); IV[TRI]=0; return 0; }
  }
  IV[TRI]=0;
  printf("nao abriu em %d ms\n", T-t0);
  return 2;
}
