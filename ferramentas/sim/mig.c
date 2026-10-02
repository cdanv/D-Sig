/* mig.c — a migracao a partir de uma EEPROM da 1.0f.
 *
 * Ate a 1.0f as SPVARs 61-63 guardavam a configuracao do MOD 21. Na 1.0h elas guardam a
 * permutacao. Um Cronus que vem da 1.0f chega com elas em um de tres estados: zeradas
 * (MOD 21 nunca configurado — o caso do Daniel), com configuracao real de MOD, ou com
 * lixo. Nos tres o guarda tem de RECUSAR e a identidade tem de entrar.
 *
 * Nao se testa aqui "recuperar o que o aparelho tinha feito": a permutacao e o unico
 * registro disso, e se ela e destruida a informacao acabou. O que se exige e que o
 * resultado seja CONSISTENTE, nao que seja adivinhado.
 *
 * uso: mig <eeprom.bin> <w61> <w62> <w63>
 *      devolve 0 se a permutacao saiu identidade e valida.
 */
#include "gpcrt.h"
#include <string.h>
int IV[64], OV[64], PV[64], PT[64], RT=10, PVAR[128]; long OPS=0;
int RUMB=0, RUMBF=0, LEDS[4]; int SCREEN=0, CLS=0, PRINTS=0; long NGET=0, NSET=0;
void gpc_init(void); void gpc_main(void);
int Perm_Carga(int s); int Perm_Valida(void);
static void step(int n){int i,t; for(t=0;t<n;t++){
  for(i=0;i<64;i++){ if((IV[i]!=0)!=(PV[i]!=0))PT[i]=0; else PT[i]+=RT; OV[i]=IV[i]; }
  gpc_main(); for(i=0;i<64;i++)PV[i]=IV[i]; }}
int main(int c, char **v){
  if(c<5){ fprintf(stderr,"uso: mig <eeprom> <w61> <w62> <w63>\n"); return 2; }
  FILE *f=fopen(v[1],"rb");
  if(!f){ fprintf(stderr,"nao abriu %s\n",v[1]); return 2; }
  if(fread(PVAR,sizeof(int),128,f)!=128){ fclose(f); return 2; } fclose(f);
  PVAR[61]=atoi(v[2]); PVAR[62]=atoi(v[3]); PVAR[63]=atoi(v[4]);
  gpc_init();
  step(40);                                  /* o Boot_Persistir precisa terminar */
  int s, ident=1;
  for(s=1;s<=20;s++) if(Perm_Carga(s)!=s) ident=0;
  printf("identidade=%d valida=%d gravado=[%d,%d,%d]\n",
         ident, Perm_Valida(), PVAR[61], PVAR[62], PVAR[63]);
  return (ident && Perm_Valida()) ? 0 : 1;
}
