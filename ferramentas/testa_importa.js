// O importador de backup do Cronus, exercitado pelo app de verdade (jsdom).
//
//   node testa_importa.js gera <index.html> <semente>   -> JSON {slots, mods}
//   node testa_importa.js le   <index.html> <x.znbk>    -> JSON do importaZnbk()
//
// Quem monta o .znbk entre os dois passos e o testa_sim.py, com o zipfile do Python —
// assim o leitor de ZIP do app e testado contra um ZIP que ele nao escreveu.
// Pseudoaleatorio com semente: a mesma rodada reprova do mesmo jeito.
const { JSDOM } = require('jsdom');
const fs = require('fs');
const [modo, app, arg] = process.argv.slice(2);
const w = new JSDOM(fs.readFileSync(app, 'utf8'), {
  runScripts: 'dangerously', url: 'http://localhost/',
  // o jsdom nao traz estes; o Node 20+ traz, e e o mesmo da plataforma web
  beforeParse(win) { for (const k of ['DecompressionStream', 'Response', 'Blob', 'TextDecoder']) win[k] = globalThis[k]; },
}).window;

if (modo === 'gera') {
  let s = (+arg >>> 0) || 1;
  const r = n => { s = (Math.imul(s, 1103515245) + 12345) >>> 0; return (s >>> 8) % n; };
  // 4 slots de MODs aleatorios cobrindo TODA a faixa de cada campo, 1 zerado
  // (o InLoco recem-gravado) e 1 de outro script (SPVARs fora do layout).
  const slots = [], mods = [];
  for (let k = 0; k < 4; k++) {
    const sv = [], ms = [];
    for (let i = 0; i < 20; i++) {
      const m = w.modVazio();
      Object.assign(m, { d1: r(2), d2: r(2), d3: r(2), d4: r(2), fonte: 1 + r(22), passivo: r(2),
        tipo: r(3), dst: [r(19), r(19), r(19), r(19)], tmp: [r(8), r(8), r(8), r(8)], mult: r(19),
        dir: r(3), tin: r(21), tout: r(20), gHoldM: r(2), gHoldT: r(63), delay: r(4), gAfterT: r(8),
        modo: r(4), gHold: r(17), g2clk: r(17), gTog: r(17), gAfter: r(17), lat: r(16), ciclos: r(8) });
      sv.push(...w.spvars(m)); ms.push(m);
    }
    sv.push(r(1e9), r(1e9), r(1e9), r(1e9));
    slots.push({ nome: 'Aleatorio_' + k + '_D-Sig.gpc', sv }); mods.push(ms);
  }
  slots.push({ nome: 'InLoco_D-Sig.gpc', sv: new Array(64).fill(0) });
  slots.push({ nome: 'Outro_script.gpc', sv: new Array(64).fill(-1) });
  console.log(JSON.stringify({ slots, mods }));
} else if (modo === 'le') {
  w.lerZnbk(new Uint8Array(fs.readFileSync(arg))).then(sl => {
    const r = w.importaZnbk(sl);
    console.log(JSON.stringify({ jogos: r.jogos.map(x => ({ nome: x.jogo.nome, mods: x.jogo.mods })), pulos: r.pulos }));
  }).catch(e => { console.error(e.stack); process.exit(1); });
} else {
  console.error('uso: node testa_importa.js gera|le <index.html> <semente|x.znbk>'); process.exit(2);
}
