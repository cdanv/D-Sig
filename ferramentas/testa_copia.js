// Copiar e colar um MOD, exercitado pelo app de verdade (jsdom).
//
// O QUE PODE DAR ERRADO NUMA COPIA, e e o que cada bloco confere:
//   - a copia e o original serem o MESMO objeto (editar um edita o outro);
//   - o ZETA da copia apontar para o MOD errado depois de apagar/reordenar no intervalo;
//   - o ZETA ir junto para OUTRO jogo, onde os numeros sao de outros MODs;
//   - a colagem abrir BURACO na lista ou estourar o teto de MODs;
//   - o MOD colado gerar SPVARs diferentes das do original.
// E, no fim, pelos BOTOES: o caminho que o usuario faz.
//
// uso: node testa_copia.js <index.html> <cfg.json>     sai 0 se tudo bate
const { JSDOM } = require('jsdom');
const fs = require('fs');
const [APP, LIB] = process.argv.slice(2);
if (!LIB) { console.error('uso: node testa_copia.js <index.html> <cfg.json>'); process.exit(2); }
function abre() {
  const lib = JSON.parse(fs.readFileSync(LIB, 'utf8'));
  const dom = new JSDOM(fs.readFileSync(APP, 'utf8'), {
    runScripts: 'dangerously', url: 'https://cdanv.github.io/D-Sig/',
    beforeParse(w) { const st = { dsig: JSON.stringify(lib) };
      Object.defineProperty(w, 'localStorage', { value: { getItem: k => k in st ? st[k] : null,
        setItem: (k, v) => { st[k] = String(v); }, removeItem: k => { delete st[k]; } } });
      w.matchMedia = () => ({ matches: false, addListener() {}, addEventListener() {} });
      w.navigator.serviceWorker = { register: () => Promise.resolve() };
      w.__alertas = []; w.alert = m => w.__alertas.push(String(m)); w.__st = st; } });
  return dom.window;
}
let falhas = 0;
function ver(nome, ok, det) { if (!ok) falhas++; console.log(`  ${ok ? 'ok ' : 'NAO'}  ${nome}${det ? '   ' + det : ''}`); }
const usados = (w, j) => j.mods.map((m, k) => w.nomeMod(j, k) ? k : -1).filter(k => k >= 0);
const semNota = m => { const c = JSON.parse(JSON.stringify(m)); delete c.nota; return JSON.stringify(c); };

// ---- 1. mesmo jogo: copia fiel, independente, na primeira vaga -------------------
{
  const w = abre(), j = w.D.jogos[0];
  // abre vaga: o molde pode estar cheio
  while (usados(w, j).length > 17) w.apagarMod(j, usados(w, j).length - 1);
  const src = usados(w, j).find(k => j.mods[k].excl.length + j.mods[k].assoc.length + j.mods[k].bloq.length > 0);
  ver('o molde tem um MOD com ZETA para copiar', src !== undefined);
  const antes = JSON.stringify(j.mods[src]), n0 = usados(w, j).length, vaga = w.vagaMod(j);
  w.copiaMod(j, src);
  const c = w.colaMod(j);
  ver('cola na primeira vaga', c && c.i === vaga && vaga === n0, `vaga ${vaga}, colou em ${c && c.i}`);
  ver('a lista continua sem buraco e com NMOD posicoes',
    usados(w, j).join() === [...Array(n0 + 1).keys()].join() && j.mods.length === w.NMOD);
  ver('o original nao mudou', JSON.stringify(j.mods[src]) === antes);
  ver('a copia e igual ao original (fora a anotacao)', semNota(j.mods[c.i]) === semNota(j.mods[src]));
  ver('as SPVARs da copia sao as do original', w.spvars(j.mods[c.i]).join() === w.spvars(j.mods[src]).join());
  ver('nenhuma relacao ficou para tras no mesmo jogo', c.semZeta === 0);
  j.mods[c.i].dst[0] = (j.mods[c.i].dst[0] + 1) % 19; j.mods[c.i].excl.push(0); j.mods[c.i].tmp[1] = 7;
  ver('editar a copia nao edita o original', JSON.stringify(j.mods[src]) === antes);
  const c2 = w.colaMod(j);
  ver('colar de novo traz o MOD como estava AO COPIAR', c2 && semNota(j.mods[c2.i]) === semNota(JSON.parse(antes)));
  // e o ORIGINAL mudando depois de copiado: a copia e a fotografia da hora, nao um atalho
  j.mods[src].tipo = (j.mods[src].tipo + 1) % 3; j.mods[src].dst[1] = 4; j.mods[src].lat = 9;
  const c4 = w.colaMod(j);
  ver('mexer no original DEPOIS de copiar nao muda o que se cola',
    c4 && semNota(j.mods[c4.i]) === semNota(JSON.parse(antes)));
  ver('nenhum MOD aponta para si mesmo', j.mods.every((m, k) => ['excl', 'assoc', 'bloq'].every(r => m[r].indexOf(k) < 0)));
  // a biblioteca resultante atravessa a normalizacao sem ser tocada
  const s1 = JSON.stringify(w.D); w.normaliza(w.D);
  ver('a biblioteca com a copia passa intacta pela normalizacao', JSON.stringify(w.D) === s1);
  let gerou = ''; try { gerou = w.scriptCompleto(j); } catch (e) { gerou = ''; }
  ver('o script e gerado com a copia', /\nmain \{/.test(gerou) &&
    new RegExp('DS_A_' + String(c.i + 1).padStart(2, '0') + '=' + w.spvars(j.mods[c.i])[0] + ';').test(gerou));
}

// ---- 2. apagar e reordenar ENTRE copiar e colar: o ZETA acompanha o MOD ----------
{
  const w = abre(), j = w.D.jogos[0];
  while (usados(w, j).length > 17) w.apagarMod(j, usados(w, j).length - 1);
  // um MOD que aponte para alvos de indice >= 2, para o delete do MOD 0 desloca-los
  const src = usados(w, j).find(k => k >= 2 && ['excl', 'assoc', 'bloq'].some(r => j.mods[k][r].some(t => t >= 2)));
  ver('o molde tem um MOD com ZETA em alvo deslocavel', src !== undefined);
  const alvosObj = {}; ['excl', 'assoc', 'bloq'].forEach(r => alvosObj[r] = j.mods[src][r].map(t => j.mods[t]));
  w.copiaMod(j, src);
  w.apagarMod(j, 0);                       // tudo desce uma posicao
  w.trocaMod(j, 2, 3);                     // e dois trocam de lugar
  const c = w.colaMod(j);
  const esperado = {}; ['excl', 'assoc', 'bloq'].forEach(r =>
    esperado[r] = alvosObj[r].map(o => j.mods.indexOf(o)).filter(t => t >= 0));
  ver('depois de apagar e reordenar, o ZETA da copia aponta para os MESMOS MODs',
    c && ['excl', 'assoc', 'bloq'].every(r => j.mods[c.i][r].slice().sort().join() === esperado[r].slice().sort().join()),
    c ? JSON.stringify({ excl: j.mods[c.i].excl, assoc: j.mods[c.i].assoc, bloq: j.mods[c.i].bloq }) : '');
  // alvo apagado sai, e e contado
  const w2 = abre(), j2 = w2.D.jogos[0];
  while (usados(w2, j2).length > 17) w2.apagarMod(j2, usados(w2, j2).length - 1);
  const s2 = usados(w2, j2).find(k => j2.mods[k].excl.length + j2.mods[k].assoc.length + j2.mods[k].bloq.length > 0);
  const rel = ['excl', 'assoc', 'bloq'].find(r => j2.mods[s2][r].length), alvo = j2.mods[s2][rel][0];
  const total = j2.mods[s2].excl.length + j2.mods[s2].assoc.length + j2.mods[s2].bloq.length;
  const vezes = ['excl', 'assoc', 'bloq'].reduce((n, r) => n + j2.mods[s2][r].filter(t => t === alvo).length, 0);
  w2.copiaMod(j2, s2); w2.apagarMod(j2, alvo);
  const c3 = w2.colaMod(j2);
  const ficou = j2.mods[c3.i].excl.length + j2.mods[c3.i].assoc.length + j2.mods[c3.i].bloq.length;
  ver('alvo apagado no intervalo sai da copia e e contado', c3.semZeta === vezes && ficou === total - vezes,
    `${total} relacoes, ${vezes} para o apagado, ficaram ${ficou}`);
}

// ---- 3. outro jogo: o MOD vai, o ZETA nao ----------------------------------------
{
  const w = abre(), j = w.D.jogos[0];
  const src = usados(w, j).find(k => j.mods[k].excl.length + j.mods[k].assoc.length + j.mods[k].bloq.length > 0);
  const total = j.mods[src].excl.length + j.mods[src].assoc.length + j.mods[src].bloq.length;
  // O destino e um jogo COM MODs nas mesmas posicoes dos alvos — um clone do primeiro.
  // Num jogo vazio o teste passaria mesmo com o ZETA indo junto, porque la nenhum alvo
  // existe; foi a sabotagem que mostrou. E no jogo cheio que o numero "serve" e engana.
  const novo = JSON.parse(JSON.stringify(j)); novo.nome = 'OUTRO'; w.D.jogos.push(novo);
  while (usados(w, novo).length > 17) w.apagarMod(novo, usados(w, novo).length - 1);
  const vagaN = w.vagaMod(novo);
  w.copiaMod(j, src);
  const c = w.colaMod(novo);
  const m = novo.mods[c.i];
  ver('em outro jogo cola na primeira vaga de la', c.i === vagaN);
  ver('em outro jogo o ZETA nao vai, e a colagem diz quantas relacoes ficaram',
    m.excl.length + m.assoc.length + m.bloq.length === 0 && c.semZeta === total, `${c.semZeta} de ${total}`);
  ver('o resto do MOD e o mesmo', w.spvars(m).join() === w.spvars(j.mods[src]).join());
}

// ---- 4. jogo cheio: nao cola, nao estraga -----------------------------------------
{
  const w = abre(), j = w.D.jogos[0];
  let k; while ((k = w.vagaMod(j)) >= 0) { j.mods[k] = JSON.parse(JSON.stringify(j.mods[0])); j.mods[k].excl = []; j.mods[k].assoc = []; j.mods[k].bloq = []; }
  const antes = JSON.stringify(j);
  w.copiaMod(j, 0);
  ver('com os 20 MODs usados a colagem e recusada e nada muda', w.colaMod(j) === null && JSON.stringify(j) === antes && j.mods.length === w.NMOD);
  ver('sem nada copiado a colagem nao faz nada', (() => { const w3 = abre(); return w3.colaMod(w3.D.jogos[0]) === null; })());
}

// ---- 5. pelos BOTOES ---------------------------------------------------------------
{
  const w = abre(), d = w.document, j = w.D.jogos[0];
  while (usados(w, j).length > 17) w.apagarMod(j, usados(w, j).length - 1);
  const botao = t => [...d.querySelectorAll('#app button')].find(b => b.textContent.trim().indexOf(t) === 0);
  w.jg = 0; w.tela = 'jogo'; w.render();
  ver('sem copia, a tela do jogo nao oferece Colar', !botao('Colar MOD copiado'));
  w.md = w.vagaMod(j); w.tela = 'mod'; w.render();
  ver('MOD em branco nao oferece Copiar', !botao('Copiar este MOD') && !!botao('Apagar este MOD'));
  const src = 1, n0 = usados(w, j).length;
  w.md = src; w.tela = 'mod'; w.render();
  const bc = botao('Copiar este MOD');
  ver('MOD configurado oferece Copiar ao lado do Apagar', !!bc && bc.parentNode === botao('Apagar este MOD').parentNode);
  bc.click();
  ver('o botao confirma a copia', /Copiado/.test(bc.textContent) && !!w.COPIA);
  d.getElementById('volta').click();
  const bp = botao('Colar MOD copiado');
  ver('a tela do jogo passa a oferecer Colar', w.tela === 'jogo' && !!bp && !bp.disabled);
  bp.click();
  ver('colar abre o editor do MOD novo', w.tela === 'mod' && w.md === n0 && usados(w, j).length === n0 + 1);
  ver('e a biblioteca foi gravada com ele', JSON.parse(w.__st.dsig).jogos[0].mods[n0].fonte === j.mods[src].fonte &&
    w.spvars(JSON.parse(w.__st.dsig).jogos[0].mods[n0]).join() === w.spvars(j.mods[src]).join());
}
console.log(falhas ? `\n${falhas} conferencia(s) reprovaram` : '\ncopiar e colar: tudo bate');
process.exit(falhas ? 1 : 0);
