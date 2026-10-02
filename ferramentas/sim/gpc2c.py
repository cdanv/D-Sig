import re,sys
src=open(sys.argv[1],encoding='utf-8').read()
out=[]; protos=[]; combos=[]
# strip comments first to make regex simple (keep line count irrelevant)
s=re.sub(r'/\*.*?\*/','',src,flags=re.S)
# CORRIGIDO: o re.sub cego cortava um "//" que estivesse DENTRO de uma string — um nome
# de jogo como 'AC//Origins' virava const char* sem fechar as aspas, e o erro aparecia
# no gcc como se o .gpc estivesse errado. Agora a varredura respeita as aspas.
def _tira_com(txt):
    saida=[]
    for lin in txt.split('\n'):
        fora=True; corte=-1
        for k,c in enumerate(lin):
            if c=='"': fora=not fora
            elif fora and c=='/' and k+1<len(lin) and lin[k+1]=='/': corte=k; break
        saida.append(lin[:corte] if corte>=0 else lin)
    return '\n'.join(saida)
s=_tira_com(s)
lines=s.split('\n'); res=[]
for l in lines:
    m=re.match(r'\s*define\s+(\w+)\s*=\s*(.*?);\s*$',l)
    if m: res.append('#define %s (%s)'%(m.group(1),m.group(2))); continue
    l=re.sub(r'\bconst\s+string\s+(\w+)\s*=',r'const char *\1 =',l)
    l=re.sub(r'\bconst\s+image\s+(\w+)\s*\[\s*\]\s*=',r'const int \1[] =',l)
    m=re.match(r'\s*function\s+(\w+)\s*\((.*?)\)\s*\{(.*)$',l)
    if m:
        ps=[p.strip() for p in m.group(2).split(',') if p.strip()]
        sig='int %s(%s)'%(m.group(1),', '.join('int '+p for p in ps) or 'void')
        protos.append(sig+';'); res.append(sig+' {'+m.group(3)); continue
    m=re.match(r'\s*combo\s+(\w+)\s*\{(.*)$',l)
    if m:
        combos.append(m.group(1)); res.append('void combo_%s(void) {%s'%(m.group(1),m.group(2))); continue
    l=re.sub(r'^\s*main\s*\{','void gpc_main(void) {',l)
    l=re.sub(r'^\s*init\s*\{','void gpc_init(void) {',l)
    res.append(l)
body='\n'.join(res)
body=re.sub(r'\bcombo_run\((\w+)\)',r'combo_run_(CMB_\1)',body)
body=re.sub(r'\bcombo_stop\((\w+)\)',r'combo_stop_(CMB_\1)',body)
body=re.sub(r'\bcombo_running\((\w+)\)',r'combo_running_(CMB_\1)',body)
hdr='#include "gpcrt.h"\n'+''.join('#define CMB_%s %d\n'%(c,i) for i,c in enumerate(combos))
hdr+='\n'.join(protos)+'\n'+''.join('void combo_%s(void);\n'%c for c in combos)
open(sys.argv[2],'w').write(hdr+body)
