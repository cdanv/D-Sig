#!/usr/bin/env python3
"""Verificador estrutural do GPC.
Pega o que a contagem de chaves NAO pega: else orfao, blocos mal aninhados.
Foi um else orfao — introduzido ao inserir codigo no meio de uma cadeia else-if —
que passou por todas as checagens e so o ZenStudio acusou."""
import re, sys

def checa(path):
    bruto = open(path, encoding='utf-8', errors='replace').read()
    c = re.sub(r'/\*.*?\*/', '', bruto, flags=re.S)
    c = re.sub(r'//[^\n]*', '', c)
    linhas = c.split('\n')
    prob = []

    for i, l in enumerate(linhas):
        s = l.strip()
        if not re.match(r'^else\b', s):
            continue                      # '} else' e sempre valido
        j = i - 1
        while j >= 0 and not linhas[j].strip():
            j -= 1
        if j < 0:
            prob.append((i+1, "else no inicio do arquivo", s[:70])); continue
        ant = linhas[j].strip()
        # valido se o anterior fecha um bloco, OU e um if de uma linha so
        if ant.endswith('}') or re.search(r'\bif\s*\(', ant):
            continue
        prob.append((i+1, "ELSE ORFAO — o comando anterior nao e um if", s[:70]))

    d = 0
    for i, l in enumerate(linhas):
        d += l.count('{') - l.count('}')
        if d < 0:
            prob.append((i+1, "fecha mais chaves do que abriu", l.strip()[:70])); break
    if d != 0:
        prob.append((len(linhas), f"arquivo termina com profundidade {d}", ""))

    for n, a, b in [("parenteses", '(', ')'), ("colchetes", '[', ']')]:
        if c.count(a) != c.count(b):
            prob.append((0, f"{n} desbalanceados: {c.count(a)} x {c.count(b)}", ""))

    fn = set(re.findall(r'^function\s+(\w+)', bruto, re.M))
    gpc = {'if','while','return','set_val','get_ival','get_ptime','event_press',
           'event_release','abs','combo_run','set_pvar','get_pvar','cls_oled','rect_oled',
           'set_led','set_rumble','reset_rumble','wait','get_rtime','print','main','init',
           'function','combo','else','for','update_leds','colorled'}
    for x in sorted(set(re.findall(r'\b([A-Za-z_]\w*)\s*\(', c)) - fn - gpc):
        prob.append((0, f"chamada sem definicao: {x}", ""))

    print(f"--- {path.split('/')[-1]}")
    if prob:
        for ln, msg, tx in prob:
            print(f"  linha {ln:5d}  {msg}" + (f"  |  {tx}" if tx else ""))
        return 1
    print("  ok — sem else orfao, chaves equilibradas, sem chamada perdida")
    return 0

sys.exit(sum(checa(p) for p in sys.argv[1:]))
