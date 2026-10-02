#include "gpcrt.h"
int IV[64], OV[64], PV[64], PT[64], RT=10, PVAR[128]; long OPS=0;
int RUMB=0, RUMBF=0, LEDS[4];
int SCREEN=0, CLS=0, PRINTS=0;
long NGET=0, NSET=0;
void gpc_init(void); void gpc_main(void); int Switch_Mode(int m);
extern int CurrentMode;
int main(int c,char**v){ int N=atoi(v[1]),t,i; srand(atoi(v[2])); gpc_init(); Switch_Mode(1);
 unsigned long h=0;
 for(t=0;t<N;t++){
   if(rand()%7==0){ int b=rand()%16; if(b==3||b==16) b=6; IV[b]=!IV[b]*((b==1||b==4)?(rand()%101):1); }
   if(rand()%5==0){ int a=18+rand()%4; IV[a]=(rand()%201)-100; }
   if(rand()%9==0){ IV[24]=rand()%1920; IV[25]=rand()%1080; }
   if(t%3000==1500) Switch_Mode(1+(rand()%4));
   for(i=0;i<64;i++){ if((IV[i]!=0)!=(PV[i]!=0))PT[i]=0; else PT[i]+=10; OV[i]=IV[i]; }
   gpc_main();
   for(i=0;i<32;i++) { h=h*1000003u+(unsigned)OV[i]; if(v[3]&&t<N) printf("%d %d %d\n",t,i,OV[i]); }
   for(i=0;i<64;i++)PV[i]=IV[i]; }
 fprintf(stderr,"hash %lu\n",h); return 0;}
