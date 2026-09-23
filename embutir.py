#!/usr/bin/env python3
# Embute o D-Sig.gpc no index.html e prova que os dois ficaram byte a byte iguais.
# Roda sempre que o .gpc mudar: o app e a fonte de verdade, e divergencia entre o avulso
# e o template embutido gera scripts inconsistentes sem dar nenhum sinal.
import re, hashlib, sys

gpc = open('D-Sig.gpc', encoding='utf-8').read()
s = open('index.html', encoding='utf-8').read()
m = re.search(r'(<script type="text/plain" id="tpl">)(.*?)(</script>)', s, re.S)
assert m, 'template nao encontrado no index.html'
antes = len(m.group(2))
s = s[:m.start(2)] + gpc + s[m.end(2):]
open('index.html', 'w', encoding='utf-8').write(s)

tpl = re.search(r'<script type="text/plain" id="tpl">(.*?)</script>',
                open('index.html', encoding='utf-8').read(), re.S).group(1)
h1 = hashlib.sha256(gpc.encode()).hexdigest()
h2 = hashlib.sha256(tpl.encode()).hexdigest()
print(f'  template: {antes} -> {len(gpc)} bytes')
print(f'  D-Sig.gpc       sha256 {h1[:32]}')
print(f'  template no app sha256 {h2[:32]}')
if h1 != h2:
    print('  DIVERGEM'); sys.exit(1)
print('  => byte a byte identicos')

# o template nao pode conter "</script>", que fecharia a tag antes da hora
assert '</script>' not in gpc, 'o .gpc contem </script> e quebraria o HTML'
print('  => sem "</script>" dentro do template')
