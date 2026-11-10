#!/usr/bin/env python3
"""Verificador estrutural do GPC.
Pega o que a contagem de chaves NAO pega: else orfao, blocos mal aninhados.
Foi um else orfao — introduzido ao inserir codigo no meio de uma cadeia else-if —
que passou por todas as checagens e so o ZenStudio acusou."""
import re, sys

def so_codigo(t):
    """Tira comentarios e ESVAZIA strings ("abc" -> ""), preservando as quebras de linha.

    Varredura caractere a caractere, e nao duas regex: as regex tratavam o que esta entre
    aspas como codigo. Um nome de jogo como "VAZIO (molde)", que o app parte em duas
    const string de 10 caracteres, deixava um parentese sozinho em cada metade e o
    verificador acusava "parenteses desbalanceados" e "chamada sem definicao: VAZIO".
    E um /* dentro de um nome apagaria codigo de verdade ate o proximo */. Achado na
    auditoria de 10/11, com o molde vazio do proprio portao."""
    out, i, n = [], 0, len(t)
    while i < n:
        ch = t[i]
        if ch == '"':                                   # string: guarda so as aspas
            j = i + 1
            while j < n and t[j] != '"' and t[j] != '\n':
                j += 2 if t[j] == '\\' else 1
            out.append('""')
            i = j + 1
        elif t.startswith('//', i):                     # comentario de linha
            while i < n and t[i] != '\n':
                i += 1
        elif t.startswith('/*', i):                     # comentario de bloco
            j = t.find('*/', i + 2)
            j = n if j < 0 else j + 2
            out.append('\n' * t.count('\n', i, j))      # mantem a numeracao das linhas
            i = j
        else:
            out.append(ch)
            i += 1
    return ''.join(out)


def checa(path):
    bruto = open(path, encoding='utf-8', errors='replace').read()
    c = so_codigo(bruto)
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
           # nativas de desenho que o script usa desde antes da 1.0.12; sem elas o
           # verificador reprovava todo arquivo e, fora do portao, ninguem via
           'line_oled','image_oled',
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
