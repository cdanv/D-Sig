// Prova que os nomes de dominio chegam ao script pelas DUAS vias do app com o MESMO
// valor, e que o limite de 9 caracteres e o saneamento valem.
//
// POR QUE ISTO E PORTAO, e nao conferencia de uma vez: o app tem duas vias para o
// script. O codigo(j) gera o bloco para colar a mao; o scriptCompleto(j) gera o script
// inteiro. Quando este recurso foi implementado, descobriu-se que elas JA discordavam —
// o codigo() emitia MODE_S1 = "D1" e o scriptCompleto nao tocava nas ancoras. Duas vias
// para o mesmo dado e exatamente onde a divergencia mora, e ela nao da sinal.
//
// O limite de 9 vem da tela: print(12,25,1,1,...), fonte 1 a 12 px por caractere, de
// x=12 a x=127 sao 116 px.
const { JSDOM } = require('jsdom');
const fs = require('fs');
const [APP, LIB] = process.argv.slice(2);
if (!LIB) { console.error('uso: node testa_dom.js <index.html> <cfg.json>'); process.exit(2); }
const lib = JSON.parse(fs.readFileSync(LIB, 'utf8'));
const dom = new JSDOM(fs.readFileSync(APP, 'utf8'), {
  runScripts:'dangerously', url:'https://cdanv.github.io/D-Sig/',
  beforeParse(w){ const st={dsig:JSON.stringify(lib)};
    Object.defineProperty(w,'localStorage',{value:{getItem:k=>k in st?st[k]:null,
      setItem:(k,v)=>{st[k]=String(v)},removeItem:k=>{delete st[k]}}});
    w.matchMedia=()=>({matches:false,addListener(){},addEventListener(){}});
    w.navigator.serviceWorker={register:()=>Promise.resolve()}; }});
const w = dom.window;
const j = w.D.jogos[0];
if(!j){console.error('o app nao carregou a configuracao');process.exit(1)}

const casos = [
  ['Combate',        'Combate',   'normal'],
  ['Direcao',        'Direcao',   'normal'],
  ['NomeMuitoLongo', 'NomeMuito', 'cortado em 9'],
  [String.fromCharCode(65,114,34,109,97,92,88), 'Ar ma X', 'aspas e barra viram espaco'],
];
j.dom = casos.map(c=>c[0]);

const t = w.scriptCompleto(j);
const c = w.codigo(j);
console.log(`${'entrada'.padEnd(18)} ${'esperado'.padEnd(11)} ${'scriptCompleto'.padEnd(15)} ${'codigo()'.padEnd(11)} ok`);
console.log('-'.repeat(74));
let tudo = true;
casos.forEach(function(cs,i){
  const re = new RegExp('const string MODE_S'+(i+1)+'      = "([^"]*)";');
  const a = (t.match(re)||[])[1];
  const b = (c.match(re)||[])[1];
  const ok = a===cs[1] && b===cs[1];
  if(!ok) tudo=false;
  console.log(`${JSON.stringify(cs[0]).padEnd(18)} ${JSON.stringify(cs[1]).padEnd(11)} ${JSON.stringify(a).padEnd(15)} ${JSON.stringify(b).padEnd(11)} ${ok?'sim':'NAO'}`);
});
// vazio -> o padrao do template
j.dom = ['','','',''];
const t2 = w.scriptCompleto(j);
const vaz = [1,2,3,4].map(i=>(t2.match(new RegExp('MODE_S'+i+'      = "([^"]*)"'))||[])[1]);
const okv = vaz.join(',')==='Dominio_1,Dominio_2,Dominio_3,Dominio_4';
console.log(`\nvazio -> padrao do template: ${vaz.join(', ')}  ${okv?'ok':'ERRADO'}`);
// GAME_NAME_3/4 nao podem mais sair do codigo()
const g34 = /GAME_NAME_[34]/.test(c);
console.log(`codigo() emite GAME_NAME_3 ou _4: ${g34?'SIM — ERRADO':'nao'}`);
process.exit(tudo && okv && !g34 ? 0 : 1);
