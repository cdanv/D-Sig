// Gera um script CONFIGURADO a partir do index.html atual, para o simulador testar.
//
// POR QUE PASSAR PELO APP e nao escrever um .gpc de teste a mao: o que precisa ser
// testado e o par template+gerador. Um .gpc escrito a mao testaria so o template, e foi
// justamente a divergencia entre app e script que produziu os bugs mais caros deste
// projeto (o FA_Cfg que nao compilava, o tmp diferente entre biblioteca e script).
//
// A CONFIGURACAO E CONGELADA em sim_cfg.json. Se ela viesse da biblioteca.json viva, as
// expectativas do teste mudariam junto com os dados e o teste viraria espelho.
//
// uso: node sim_gera.js <index.html> <sim_cfg.json> <saida.gpc>
const { JSDOM } = require('jsdom');
const fs = require('fs');

const [APP, CFG, SAI] = process.argv.slice(2);
if (!APP || !CFG || !SAI) { console.error('uso: node sim_gera.js app cfg saida'); process.exit(2); }

const dom = new JSDOM(fs.readFileSync(APP, 'utf8'), {
  runScripts: 'dangerously', url: 'https://cdanv.github.io/D-Sig/',
  beforeParse(w) {
    const s = { dsig: fs.readFileSync(CFG, 'utf8') };
    Object.defineProperty(w, 'localStorage', { value: {
      getItem: k => (k in s ? s[k] : null),
      setItem: (k, v) => { s[k] = String(v); },
      removeItem: k => { delete s[k]; } } });
    w.matchMedia = () => ({ matches: false, addListener() {}, addEventListener() {} });
    w.navigator.serviceWorker = { register: () => Promise.resolve() };
  } });

const w = dom.window;
if (!w.D || !w.D.jogos || !w.D.jogos.length) { console.error('ERRO: o app nao carregou a configuracao'); process.exit(1); }
const j = w.D.jogos[0];
const t = w.scriptCompleto(j);
if (!t || t.indexOf('function Config_Inicial() {') < 0) { console.error('ERRO: script gerado sem Config_Inicial'); process.exit(1); }
if (t.indexOf('//') >= 0) { console.error('ERRO: o script gerado tem comentario'); process.exit(1); }
fs.writeFileSync(SAI, t);
console.log(`gerado: ${j.nome} -> ${SAI} (${t.split('\n').length} linhas)`);
