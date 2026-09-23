#!/usr/bin/env python3
"""Remove os comentarios de um .gpc, preservando o codigo linha a linha.

POR QUE LINHA A LINHA, E NAO MINIFICANDO: o app monta o script gerado por ANCORAS de
texto — ele procura 'const string GAME_NAME_1  = "-TITULO-";', 'function update_leds() {',
'int Cfg_Selo = 0;', 'function Config_Inicial() {' e 'function Config_Zeta() {' e substitui
esses trechos. Juntar linhas, reindentar ou mexer no espacamento interno de uma dessas
linhas quebraria a geracao em silencio: o replace simplesmente nao acha nada e o script
sai sem a configuracao. Por isso o removedor NAO toca em nenhuma linha de codigo — so
apaga o que e comentario e as linhas que ficaram vazias.
"""
import re, sys

ANCORAS = [
    'const string GAME_NAME_1  = "-TITULO-";',
    'const string GAME_NAME_2  = "-TITULO-";',
    'const string GAME_NAME_3  = "-TITULO-";',
    'const string GAME_NAME_4  = "-TITULO-";',
    'function update_leds() {',
    'CurrentMode == 4',
    'int Cfg_Selo = 0;',
    'function Config_Inicial() {',
    'function Config_Zeta() {',
]


def limpar(txt):
    saida = []
    em_bloco = False
    for linha in txt.split('\n'):
        if em_bloco:
            if '*/' in linha:
                em_bloco = False
                resto = linha.split('*/', 1)[1]
                if resto.strip():
                    saida.append(resto.rstrip())
            continue
        # comentario de bloco que ABRE nesta linha
        if '/*' in linha:
            antes, depois = linha.split('/*', 1)
            if '*/' in depois:
                linha = antes + depois.split('*/', 1)[1]
            else:
                em_bloco = True
                if antes.strip():
                    saida.append(antes.rstrip())
                continue
        # comentario de linha — fora de string. Nenhuma string deste arquivo contem "//"
        # (conferido), mas a varredura respeita as aspas de todo modo.
        fora, i, n = True, 0, len(linha)
        corte = -1
        while i < n:
            c = linha[i]
            if c == '"':
                fora = not fora
            elif fora and c == '/' and i + 1 < n and linha[i + 1] == '/':
                corte = i
                break
            i += 1
        if corte >= 0:
            linha = linha[:corte]
        if linha.strip():
            saida.append(linha.rstrip())
    return '\n'.join(saida) + '\n'


if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    bruto = open(src, encoding='utf-8').read()
    limpo = limpar(bruto)

    # --- verificacoes que fazem o script falhar em vez de entregar algo errado ---
    for a in ANCORAS:
        assert a in limpo, f'ANCORA PERDIDA: {a!r}'
    assert '//' not in limpo.replace('http://', '').replace('https://', ''), 'sobrou //'
    assert '/*' not in limpo and '*/' not in limpo, 'sobrou comentario de bloco'

    # o codigo tem de ser o MESMO: comparo as linhas de codigo das duas versoes
    def codigo(t):
        return [l for l in limpar(t).split('\n') if l.strip()]
    assert codigo(bruto) == [l for l in limpo.split('\n') if l.strip()], 'codigo mudou'

    # chaves, parenteses e o numero de funcoes
    for nome, ab, fe in [('chaves', '{', '}'), ('parenteses', '(', ')')]:
        assert limpo.count(ab) == limpo.count(fe), f'{nome} desbalanceados'
    nf_a = len(re.findall(r'^function\s+(\w+)', bruto, re.M))
    nf_b = len(re.findall(r'^function\s+(\w+)', limpo, re.M))
    assert nf_a == nf_b, f'funcoes: {nf_a} -> {nf_b}'

    open(dst, 'w', encoding='utf-8').write(limpo)
    la, lb = bruto.count('\n') + 1, limpo.count('\n') + 1
    print(f'  {src} -> {dst}')
    print(f'  linhas : {la} -> {lb}  (-{100 - 100 * lb // la}%)')
    print(f'  bytes  : {len(bruto)} -> {len(limpo)}  (-{100 - 100 * len(limpo) // len(bruto)}%)')
    print(f'  funcoes: {nf_b}, todas preservadas; {len(ANCORAS)} ancoras do app intactas')
