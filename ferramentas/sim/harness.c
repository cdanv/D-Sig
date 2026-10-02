#include "gpcrt.h"
#include <string.h>
int IV[64], OV[64], PV[64], PT[64], RT=10, PVAR[128];
long OPS=0;
int RUMB=0, RUMBF=0, LEDS[4];
int SCREEN=0, CLS=0, PRINTS=0;
long NGET=0, NSET=0;
void gpc_init(void); void gpc_main(void); int Switch_Mode(int m);
extern int CurrentMode;
/* scenario from stdin: lines "t btn val" (btn index), then "END T" ; watch list via argv */
typedef struct {int t,b,v;} Ev;
Ev ev[1000]; int nev=0;
int main(int argc,char**argv){
  int T=0,i,k; char w[32];
  while(scanf("%31s",w)==1){
    if(!strcmp(w,"END")){scanf("%d",&T);break;}
    ev[nev].t=atoi(w); scanf("%d %d",&ev[nev].b,&ev[nev].v); nev++;
  }
  int nw=argc-1, wb[16], last[16];
  for(i=0;i<nw;i++){wb[i]=atoi(argv[i+1]);last[i]=-999;}
  gpc_init(); Switch_Mode(1);
  int t; k=0;
  for(t=0;t<=T;t+=RT){
    while(k<nev && ev[k].t<=t){ IV[ev[k].b]=ev[k].v; k++; }
    for(i=0;i<64;i++){ if((IV[i]!=0)!=(PV[i]!=0)) PT[i]=0; else PT[i]+=RT; OV[i]=IV[i]; }
    gpc_main();
    for(i=0;i<nw;i++) if(OV[wb[i]]!=last[i]){ printf("%6d out%d=%d\n",t,wb[i],OV[wb[i]]); last[i]=OV[wb[i]]; }
    for(i=0;i<64;i++) PV[i]=IV[i];
  }
  return 0;
}
