// Prova que os nomes de DOMINIO e o nome do JOGO chegam ao script pelas DUAS vias do
// app com o MESMO valor, que os limites de tela valem (9 e 17 caracteres) e que o
// saneamento e a quebra do nome do jogo fazem o que dizem.
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
// 1.0.18: os quatro dominios acima sao os de sempre; estes entram numa SEGUNDA rodada,
// porque sao quatro por jogo. "/*" abria comentario de bloco no limparGpc e o script
// gerado saia com QUATRO linhas; letra acentuada ia crua para um print que so desenha
// ASCII. O 3o confere tambem que o script continua INTEIRO depois do nome.
const casos2 = [
  ['A p\u00e9',       'A pe',      'acento vira a letra sem acento'],
  ['Ve\u00edculo',    'Veiculo',   'idem, e continua com 7 colunas'],
  ['a/*b',            'a/ b',      'abre-comentario nao abre comentario'],
  ['x*/y\u00e7\u00e3o', 'x /ycao',   'fecha-comentario e cedilha'],
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
{
  j.dom = casos2.map(c=>c[0]);
  const t5 = w.scriptCompleto(j), c5 = w.codigo(j);
  casos2.forEach(function(cs,i){
    const re = new RegExp('const string MODE_S'+(i+1)+'      = "([^"]*)";');
    const a = (t5.match(re)||[])[1], b = (c5.match(re)||[])[1];
    const ok = a===cs[1] && b===cs[1];
    if(!ok) tudo=false;
    console.log(`${JSON.stringify(cs[0]).padEnd(18)} ${JSON.stringify(cs[1]).padEnd(11)} ${String(JSON.stringify(a)).padEnd(15)} ${String(JSON.stringify(b)).padEnd(11)} ${ok?'sim':'NAO'}`);
  });
  // o script tem de sair INTEIRO e so com ASCII: um comentario aberto por engano corta
  // tudo o que vem depois, e o main e a ultima coisa que se perde de vista.
  const inteiro = /\nmain \{/.test(t5) && /function Config_Zeta\(\) \{/.test(t5) && !/[^\x00-\x7f]/.test(t5);
  if(!inteiro) tudo=false;
  console.log(`script inteiro e so ASCII com esses nomes: ${inteiro?'sim':'NAO'}`);
  // a ANOTACAO de um MOD vira comentario de linha; "/*" nela engolia os MODs seguintes
  const jn = JSON.parse(JSON.stringify(j));
  jn.dom = ['','','',''];
  const usados = jn.mods.map((m,k)=>w.nomeMod(jn,k)?k:-1).filter(k=>k>=0);
  let okNota = usados.length >= 2;
  if(okNota){
    // fora a linha do selo: a anotacao entra no hash dos MODs, entao o selo muda mesmo
    const semSelo = t => t.replace(/^int Cfg_Selo = -?\d+;$/m, 'int Cfg_Selo;');
    const ref = semSelo(w.scriptCompleto(jn));
    jn.mods[usados[0]].nota = 'liga /* desliga';
    jn.mods[usados[1]].nota = 'fim */ sobra';
    okNota = semSelo(w.scriptCompleto(jn)) === ref;
  }
  if(!okNota) tudo=false;
  console.log(`anotacao com /* e */ nao altera o script gerado: ${okNota?'sim':'NAO'}`);
}
// vazio -> o padrao do template
j.dom = ['','','',''];
const t2 = w.scriptCompleto(j);
const vaz = [1,2,3,4].map(i=>(t2.match(new RegExp('MODE_S'+i+'      = "([^"]*)"'))||[])[1]);
const okv = vaz.join(',')==='Dominio_1,Dominio_2,Dominio_3,Dominio_4';
console.log(`\nvazio -> padrao do template: ${vaz.join(', ')}  ${okv?'ok':'ERRADO'}`);
// GAME_NAME_3/4 nao podem mais sair do codigo()
const g34 = /GAME_NAME_[34]/.test(c);
console.log(`codigo() emite GAME_NAME_3 ou _4: ${g34?'SIM — ERRADO':'nao'}`);

// ---- O NOME DO JOGO, pelas MESMAS duas vias -------------------------------------
// Entrou com a quebra inteligente. O corte era duplicado nas duas vias, e corte
// duplicado e divergencia esperando a hora — foi onde os MODE_S discordaram na 1.0.11.
// As entradas sao os jogos reais do Cronus do Daniel, que foi onde o defeito apareceu.
const nomes = [
  ['InLoco',              'InLoco',           '',        'cabe em uma linha'],
  ['GPs e Rally',         'GPs e Rally',      '',        'cabe em uma linha'],
  ['Tomb Raiden',         'Tomb Raiden',      '',        'cabe em uma linha'],
  ['Cities Skylines',     'Cities Skylines',  '',        'cabe em uma linha'],
  ['Football-FIFA-eFoot', 'Football-FIFA-',   'eFoot',   'quebra no hifen'],
  ['Red Dead Redemption II','Red Dead',       'Redemption II', 'quebra no espaco'],
  ['ABCDEFGHIJKLMNOPQRSTUVWXYZ','ABCDEFGHIJKLMNOPQ','RSTUVWXYZ','sem separador: corte cego'],
  ['AB CDEFGHIJKLMNOPQRSTU','AB CDEFGHIJKLMNOP','QRSTU','quebra perderia texto: corte cego'],
  ['Pok\u00e9mon',         'Pokemon',          '',        'acento vira a letra sem acento'],
  ['AC/*Origins',         'AC/ Origins',      '',        'abre-comentario nao corta o script'],
  ['Cora\u00e7\u00e3o de A\u00e7o IV','Coracao de Aco IV','',  'acentuado e cabe em 17 depois de saneado'],
];
console.log(`\n${'nome do jogo'.padEnd(26)} ${'linha 1'.padEnd(18)} ${'linha 2'.padEnd(14)} via  ok`);
console.log('-'.repeat(78));
let okn = true;
nomes.forEach(function(cs){
  const jj = Object.assign({}, j, {nome: cs[0]});
  [['scriptCompleto', w.scriptCompleto(jj)], ['codigo', w.codigo(jj)]].forEach(function(via){
    const l1 = (via[1].match(/GAME_NAME_1  = "([^"]*)";/)||[])[1];
    const l2 = (via[1].match(/GAME_NAME_2  = "([^"]*)";/)||[])[1];
    const ok = l1===cs[1] && l2===cs[2];
    if(!ok) okn = false;
    console.log(`${JSON.stringify(cs[0]).padEnd(26)} ${JSON.stringify(l1).padEnd(18)} ${JSON.stringify(l2).padEnd(14)} ${via[0].slice(0,6).padEnd(6)} ${ok?'sim':'NAO ('+cs[3]+')'}`);
  });
});
// Nenhuma linha pode passar de 17: a 18a letra sai da tela (x=4 + 18*7 = 130 > 127).
const estouro = nomes.some(function(cs){
  const t3 = w.scriptCompleto(Object.assign({}, j, {nome: cs[0]}));
  return (t3.match(/GAME_NAME_[12]  = "([^"]*)";/g)||[])
         .some(l=>(l.match(/"([^"]*)"/)[1]).length > 17);
});
console.log(`\nalguma linha passa de 17 caracteres: ${estouro?'SIM — SAI DA TELA':'nao'}`);

process.exit(tudo && okv && !g34 && okn && !estouro ? 0 : 1);
