#!/usr/bin/env python3
"""A UNICA ferramenta de publicacao. Rode-a sempre que mexer no script.

D-Sig.fonte.gpc  ->  D-Sig.gpc  ->  template dentro do index.html
  (comentado)        (limpo)        (limpo, byte a byte igual ao D-Sig.gpc)

O QUE ELA GARANTE, falhando em vez de entregar algo errado:
  1. o D-Sig.gpc publicado e o template embutido no app tem o MESMO sha256;
  2. nenhum comentario sobra no que e publicado;
  3. as 9 ancoras de texto que o app usa para injetar a configuracao continuam la;
  4. as linhas de codigo do limpo sao IGUAIS, uma a uma, as do arquivo comentado.

POR QUE DOIS ARQUIVOS: comentario em GPC nao custa byte nenhum no Zen — o compilador os
descarta, e os 54.112 bytes do binario sao os mesmos com ou sem eles. O que os comentarios
custam e PESO DE DOWNLOAD do app, porque o template viaja dentro do index.html. Daí a
divisao classica entre FONTE e PUBLICADO: o comentado e onde se trabalha e se aprende, o
limpo e o que vai para o ar.
"""
import re, hashlib, sys
from limpar import limpar, ANCORAS

FONTE, PUB, APP = 'D-Sig.fonte.gpc', 'D-Sig.gpc', 'index.html'

bruto = open(FONTE, encoding='utf-8').read()
limpo = limpar(bruto)

# --- 1. o codigo nao pode ter mudado -----------------------------------------
cod_fonte = [l for l in limpar(bruto).split('\n') if l.strip()]
cod_limpo = [l for l in limpo.split('\n') if l.strip()]
assert cod_fonte == cod_limpo, 'as linhas de codigo divergiram'

# --- 2. nada de comentario, e as ancoras de pe -------------------------------
assert '/*' not in limpo and '*/' not in limpo, 'sobrou comentario de bloco'
assert '//' not in limpo, 'sobrou comentario de linha'
for a in ANCORAS:
    assert a in limpo, f'ANCORA PERDIDA: {a!r}'

# --- 3. estrutura ------------------------------------------------------------
assert limpo.count('{') == limpo.count('}'), 'chaves desbalanceadas'
assert limpo.count('(') == limpo.count(')'), 'parenteses desbalanceados'
nf = len(re.findall(r'^function\s+(\w+)', limpo, re.M))
assert nf == len(re.findall(r'^function\s+(\w+)', bruto, re.M)), 'perdeu funcao'
assert 'combo ' not in re.sub(r'//[^\n]*', '', limpo), 'apareceu combo'

open(PUB, 'w', encoding='utf-8').write(limpo)

# --- 4. embute no app e prova a identidade -----------------------------------
s = open(APP, encoding='utf-8').read()
m = re.search(r'(<script type="text/plain" id="tpl">)(.*?)(</script>)', s, re.S)
assert m, 'template nao encontrado no index.html'
antes = len(m.group(2))
open(APP, 'w', encoding='utf-8').write(s[:m.start(2)] + limpo + s[m.end(2):])

tpl = re.search(r'<script type="text/plain" id="tpl">(.*?)</script>',
                open(APP, encoding='utf-8').read(), re.S).group(1)
h1 = hashlib.sha256(limpo.encode()).hexdigest()
h2 = hashlib.sha256(tpl.encode()).hexdigest()

print(f'  fonte    : {FONTE:18s} {bruto.count(chr(10))+1:6d} linhas  {len(bruto):7d} bytes')
print(f'  publicado: {PUB:18s} {limpo.count(chr(10))+1:6d} linhas  {len(limpo):7d} bytes'
      f'  (-{100 - 100*len(limpo)//len(bruto)}%)')
print(f'  template : {antes} -> {len(tpl)} bytes')
print(f'  sha256   : {h1[:32]}')
if h1 != h2:
    print('  DIVERGEM'); sys.exit(1)
print(f'  => publicado e template identicos; {nf} funcoes; 0 comentarios; '
      f'{len(ANCORAS)} ancoras intactas')
assert '</script>' not in limpo, 'o .gpc contem </script> e quebraria o HTML'
